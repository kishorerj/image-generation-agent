from datetime import datetime
from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from google.cloud import storage
from PIL import Image as PIL
from io import BytesIO
from vertexai.preview.vision_models import (
    Image,
    ImageGenerationModel,
    StyleReferenceImage,
    SubjectReferenceImage,
)
from .... import config

client = genai.Client(vertexai=True, location="global")

generation_model = ImageGenerationModel.from_pretrained(config.IMAGEN_MODEL)
capability_model = ImageGenerationModel.from_pretrained(config.IMAGEN_CAPABILITY_MODEL)


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


def _get_user_image_bytes(tool_context: ToolContext) -> bytes | None:
    """Retrieves user's image from the conversation history."""
    if tool_context.user_content:
        for part in tool_context.user_content.parts:
            if part and part.inline_data and part.inline_data.mime_type == "image/png":
                return part.inline_data.data
    return None


async def _save_and_return_image(
    tool_context: ToolContext, image_part: types.Part
) -> dict:
    """Saves the generated image and returns the tool output."""
    counter = str(tool_context.state.get("loop_iteration", 0))
    artifact_name = f"generated_image_{counter}.png"

    if config.GCS_BUCKET_NAME and image_part.inline_data:
        save_to_gcs(tool_context, image_part.inline_data.data, artifact_name, counter)

    await tool_context.save_artifact(artifact_name, image_part)
    print(f"Image also saved as ADK artifact: {artifact_name}")

    return {
        "status": "success",
        "message": f"Image generated. ADK artifact: {artifact_name}.",
        "artifact_name": artifact_name,
    }


async def _generate_images_with_gemini(
    tool_context: ToolContext,
    imagen_prompt: str,
    intent: str,
    user_image_bytes: bytes | None,
) -> dict:
    """Generates an image using the Gemini model."""
    print("Inside _generate_with_gemini")
    contents = [types.Content(role="user", parts=tool_context.user_content.parts)]

    # If no image was uploaded by the user, load the last generated image from artifacts for editing/Q&A.
    if not user_image_bytes and intent in ("image_edition", "image_QA"):
        print("User image not found, loading artifact for editing/Q&A.")
        artifact = await tool_context.load_artifact("generated_image_0.png")
        if artifact and artifact.inline_data:
            original_pil_image = PIL.open(BytesIO(artifact.inline_data.data))
            contents = [imagen_prompt, original_pil_image]

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["TEXT", "IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_IMAGE_HATE", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_HARASSMENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_IMAGE_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
        ],
    )
    response = client.models.generate_content(
        model=config.GEMINI_IMAGE_MODEL,
        contents=contents,
        config=generate_content_config,
    )
    print("Gemini images generated")

    for candidate in response.candidates:
        if candidate and candidate.content:
            for part in candidate.content.parts:
                if (
                    part
                    and part.inline_data
                    and part.inline_data.mime_type == "image/png"
                ):
                    return await _save_and_return_image(tool_context, part)

    return {"status": "error", "message": "No images were generated by Gemini."}


async def _generate_with_imagen(
    tool_context: ToolContext,
    imagen_prompt: str,
    intent: str,
    user_image_bytes: bytes | None,
) -> dict:
    """Generates an image using the Imagen model."""
    print("Inside _generate_with_imagen")
    images = None
    common_params = {
        "prompt": imagen_prompt,
        "number_of_images": 1,
        "aspect_ratio": "9:16",
        "safety_filter_level": "block_low_and_above",
        "person_generation": "allow_adult",
    }

    if intent == "text_to_image":
        images = generation_model.generate_images(**common_params)
    elif intent in ("subject_customization", "style_customization"):
        if not user_image_bytes:
            return {
                "status": "error",
                "message": f"{intent} requires a reference image, but none was provided.",
            }

        reference_images = []
        if intent == "subject_customization":
            reference_images.append(
                SubjectReferenceImage(
                    reference_id=1,
                    image=Image(image_bytes=user_image_bytes),
                    subject_description="",
                    subject_type="SUBJECT_TYPE_DEFAULT",
                )
            )
        else:  # style_customization
            reference_images.append(
                StyleReferenceImage(
                    reference_id=2,
                    image=Image(image_bytes=user_image_bytes),
                    style_description="",
                )
            )
        images = capability_model._generate_images(
            **common_params, reference_images=reference_images
        )

    if images and images.images:
        for generated_image in images.images:
            image_bytes = generated_image._image_bytes
            report_artifact = types.Part.from_bytes(
                data=image_bytes, mime_type="image/png"
            )
            return await _save_and_return_image(tool_context, report_artifact)

    return {"status": "error", "message": "No images were generated by Imagen."}


async def render_images(
    imagen_prompt: str, model: str, intent: str, tool_context: ToolContext
):
    """
    Routes image generation to the appropriate model (Gemini or Imagen) based on the intent.
    """
    print(f"Entered render_images with model: {model}, intent: {intent}")
    try:
        if model.capitalize() == "Gemini" or model.capitalize().startswith("Gemini"):
            user_image_bytes = _get_user_image_bytes(tool_context)
            return await _generate_images_with_gemini(
                tool_context, imagen_prompt, intent, user_image_bytes
            )
        elif model.capitalize() == "Imagen":
            user_image_bytes = _get_user_image_bytes(tool_context)
            return await _generate_with_imagen(
                tool_context, imagen_prompt, intent, user_image_bytes
            )
        else:
            return {"status": "error", "message": f"Unknown model specified: {model}"}

    except Exception as e:
        print(f"An error occurred in render_images: {e}")
        return {
            "status": "error",
            "message": f"Failed to generate image due to an unexpected error: {e}",
        }
