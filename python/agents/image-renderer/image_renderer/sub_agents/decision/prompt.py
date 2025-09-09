DECISION_PROMPT = """
 Your primary objective: Your primary object is to determine the model and intent for image generation based on the user input.

    Step 1 - Recommend a MODEL:
    First, analyze the user's request, including any text and images provided. Based on this analysis, you must decide whether to recommend 'Imagen' or 
    'Gemini' Model. 
    Use the following criteria for your recommendation:

    - **Criteria for  Gemini**
      - **Characteristics:** The user's request involves real-time interaction, or live editing of an image, or fusiion of one image on the other image or visual Q&A (multimodal prompting).
      - **Recommendation:** {'model': 'Gemini 2.5 Flash Image', 'reason': 'This model is designed for real-time, multimodal prompting like visual Q&A or live editing.'}

    - **Criteria for Imagen**
      - **Characteristics:** The user's request involves deep customization using reference images for style or subject tuning to achieve brand consistency.
      - **Recommendation:** {'model': 'Imagen', 'reason': 'Best for deep customization using reference images for Style/Subject Tuning to achieve brand consistency.'}

      
    Step 2 - Determine the INTENT: 
      IF MODEL IN STEP 1 is Imagen then
      Analyze the user's request text and image and determine the appropriate customization intent of the user for the model.

        - If the user wants to stylize a person or place a product in different scenes and a reference image is provided, the intent is 'subject_customization'. 
        - If the user wants to generate an image in a specific style from a reference image or alter a photo and a reference image is provided, the intent is 'style_customization'. 
        - If the user provides a prompt to generate an image without a reference image , the intent is 'text_to_image'. Set the intent as 'text_to_image'
      
      IF MODEL IN STEP 1 is Gemini then
        - If the user wants to perform fusion of multiple images like placing an image on the other image or performing a virtual try on use case,
        the intent is 'image_fusion'. 
        - If the user wants to edit the image based on prompt, then the intent is 'image_edition'
        - If the user  Questions based on the image or performing OCR of the image then the intent is 'image_QA'.
        - If the user provides a prompt to generate an image without a reference image , the intent is 'text_to_image'. Set the intent as 'text_to_image'
        


    Step 3 - Refine User prompt for Image generation for 'text_to_image': 
    Strictly perform this step only if the intent in First Step is 'text_to_image'.
    Check if the user has provided Transform the input text into a pair of highly optimized prompts—one positive and 
    one negative—specifically designed for generating a visually compelling,
    rule-compliant lockscreen image using the Imagen3 text-to-image model (provided by Google/GCP).
    Before constructing any prompts, check if the user
    you must first analyze the 
    input text to identify or conceptualize a primary subject. This subject MUST:
    1. Be very much related to the input text presented. 
    2. Describe in detail on what we would like to represent around the primary subject,
      as-in, paint a complete picture. 
    This chosen subject will be the cornerstone of your "Image Generation Prompt". 
    
    RESPONSE:
    The response should also contain the 

    MODEL: The model identified based on the "Step 1" mentioned above.
    INTENT: The intent identified based on the "Step 2" mentioned above.



    """
