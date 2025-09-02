SCORING_PROMPT = """

      "Your task is to evaluate an image based on a set of scoring rules. Follow these steps precisely:"
      1. Invoke the get_image tool to obtain the total_score from the response json.
      2. Invoke the set_score_tool by passing the total_score obtained from the response json in step 1 to set the total_score
  
  
"""
