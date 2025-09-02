from datetime import datetime
from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from google.cloud import storage
from .... import config
from vertexai.generative_models import GenerativeModel, Part

from vertexai.preview.vision_models import (
  Image,
  ImageGenerationModel,
  GeneratedImage,
  ControlReferenceImage,
  StyleReferenceImage,
  SubjectReferenceImage,
  RawReferenceImage,
)
client = genai.Client(
    vertexai=True,
    location="global"
)

generation_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
capability_model = ImageGenerationModel.from_pretrained("imagen-3.0-capability-001")

#Generate images based on the model and Intent
#imagen_prompt The iamge generation prompt
#model : the image generation model gemini or Imagen
#intent : the intent of the user prompt
async def generate_images(imagen_prompt: str, model: str, intent: str, tool_context: ToolContext):
    print(f'Enetered generate_images functionnnn {model}, {intent}')
    images_generated= ""
    user_image_bytes = None
    try:
        # Retrieve user's image from the conversation history.
        # The user's most recent message is the last one in the history.
        # ADK structures user input as a list of "parts" (e.g., text, image).
        if tool_context.user_content:
            user_msg = tool_context.user_content
            for part in user_msg.parts:
                
                if part is not None and part.inline_data is not None and part.inline_data.mime_type == "image/png":
                    user_image_bytes = part.inline_data.data
                    break
        #check if model.capitalize startswith Gemini

        if model.capitalize == "Gemini" or model.capitalize().startswith("Gemini"):
          

            print("inside gemini flash")
    
            model = "gemini-2.5-flash-image-preview"
            contents = [
                types.Content(
                role="user",
                parts=tool_context.user_content.parts
                )
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature = 1,
                response_modalities = ["TEXT", "IMAGE"],
                safety_settings = [types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_HATE",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_DANGEROUS_CONTENT",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_HARASSMENT",
                threshold="OFF"
                ),types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_SEXUALLY_EXPLICIT",
                threshold="OFF"
                )],
            )
            images = client.models.generate_content(model=model, contents=contents, 
                                           config=generate_content_config)
            print("Gemini flash images generated")
            for candidate in images.candidates:
                if candidate is not None and candidate.content is not None:
                    for part in candidate.content.parts:
                        if part is not None and part.inline_data is not None and part.inline_data.mime_type == "image/png":

                            counter = str(tool_context.state.get("loop_iteration", 0))
                            artifact_name = f"generated_image_" + counter + ".png"

                            report_artifact = part
                            # call save to gcs function
                            if config.GCS_BUCKET_NAME:
                                save_to_gcs(tool_context, report_artifact.inline_data.data, artifact_name, counter)


                            await tool_context.save_artifact(artifact_name, report_artifact)
                            print(f"Image also saved as ADK artifact: {artifact_name}")

                            return {
                                "status": "success",
                                "message": f"Image generated .  ADK artifact: {artifact_name}.",
                                "artifact_name": artifact_name,
                            }

                
                    


        elif model.capitalize() == "Imagen":
            print("inside imagen functionn")
            if intent == "text_to_image":

                images = generation_model.generate_images(
                    prompt=imagen_prompt,
                    number_of_images=1,

                    aspect_ratio="9:16",
                    safety_filter_level="block_low_and_above",
                    person_generation="allow_adult",
                    )
        
            elif intent == "subject_customization":
                if not user_image_bytes:
                    return {
                        "status": "error",
                        "message": "Subject customization requires a reference image, but none was provided.",
                    }
                reference_images=[
                    SubjectReferenceImage(
                        reference_id=1,
                        image=Image(image_bytes=user_image_bytes),
                        subject_description="",
                        subject_type="SUBJECT_TYPE_DEFAULT",
                    ),
                    ]
                images = capability_model._generate_images(
                    prompt=imagen_prompt,
                    number_of_images=1,

                    aspect_ratio="9:16",
                    safety_filter_level="block_low_and_above",
                    person_generation="allow_adult",
                    reference_images=reference_images,
                    )
                
            elif intent == "style_customization":
                if not user_image_bytes:
                    return {
                        "status": "error",
                        "message": "Style customization requires a reference image, but none was provided.",
                    }
                reference_images=[  

                    StyleReferenceImage(
                    reference_id=2,
                    image=Image(image_bytes=user_image_bytes),
                    style_description="",)
                    ]
                images = capability_model._generate_images(
                    prompt=imagen_prompt,
                    number_of_images=1,

                    aspect_ratio="9:16",
                    safety_filter_level="block_low_and_above",
                    person_generation="allow_adult",
                    reference_images=reference_images,
                    )            
            
            images_generated = images.images   
            if images_generated is not None:
                for generated_image in images_generated:
                    # Get the image bytes
                    image_bytes = generated_image._image_bytes
                    counter = str(tool_context.state.get("loop_iteration", 0))
                    artifact_name = f"generated_image_" + counter + ".png"
                    # call save to gcs function
                    if config.GCS_BUCKET_NAME:
                        save_to_gcs(tool_context, image_bytes, artifact_name, counter)

                    # Save as ADK artifact (optional, if still needed by other ADK components)
                    report_artifact = types.Part.from_bytes(
                        data=image_bytes, mime_type="image/png"
                    )

                    await tool_context.save_artifact(artifact_name, report_artifact)
                    print(f"Image also saved as ADK artifact: {artifact_name}")

                    return {
                        "status": "success",
                        "message": f"Image generated .  ADK artifact: {artifact_name}.",
                        "artifact_name": artifact_name,
                    }
            else:
                # model_dump_json might not exist or be the best way to get error details
                
            
                return {
                    "status": "error",
                    "message": "No images generated. ",
                }

    except Exception as e:
        print(f"Error generating images: {e}")
        
        return {"status": "error", "message": "No images generated.  {e}"}


def save_to_gcs(tool_context: ToolContext, image_bytes, filename: str, counter: str):
    # --- Save to GCS ---
    storage_client = storage.Client()  # Initialize GCS client
    bucket_name = config.GCS_BUCKET_NAME

    unique_id = tool_context.state.get("unique_id", "")
    current_date_str = datetime.utcnow().strftime("%Y-%m-%d")
    unique_filename = filename
    gcs_blob_name = f"{current_date_str}/{unique_id}/{unique_filename}"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_blob_name)

    try:
        blob.upload_from_string(image_bytes, content_type="image/png")
        gcs_uri = f"gs://{bucket_name}/{gcs_blob_name}"

        # Store GCS URI in session context
        # Store GCS URI in session context
        tool_context.state["generated_image_gcs_uri_" + counter] = gcs_uri

    except Exception as e_gcs:

        # Decide if this is a fatal error for the tool
        return {
            "status": "error",
            "message": f"Image generated but failed to upload to GCS: {e_gcs}",
        }
        # --- End Save to GCS ---
