# Image Renderer Agent

This agent serves as a sophisticated image assistant that determines the optimal generative model and user intent for a variety of image-related tasks. Based on the user's request, it intelligently routes tasks to either Google's Imagen or Gemini models to handle image creation, customization, editing, and visual Q&A.

## Overview
This agent analyzes user requests containing text and/or images to select the most suitable model for the task. It distinguishes between use cases best suited for Imagen's deep style and subject customization and those better for Gemini's real-time, multimodal capabilities.

*   **Model Selection:** Intelligently chooses between 'Imagen' for deep customization and 'Gemini' for multimodal and real-time interactions.
*   **Intent Recognition:** Identifies user intent, such as `text_to_image`, `style_customization`, `subject_customization`, `image_fusion`, `image_edition`, or `image_QA`.
*   **Image Generation & Customization:** Utilizes Imagen for generating images from text or customizing them based on reference images.
*   **Image Interaction:** Leverages Gemini for editing images, fusing multiple images, or answering questions about an image.

This sample agent enables users to perform a wide range of image-related tasks through a single, intelligent interface that orchestrates powerful generative models behind the scenes.

## Agent Details

The key features of the Image Renderer Agent include:

| Feature | Description |
| --- | --- |
| **Interaction Type** | Workflow |
| **Complexity**  | Medium |
| **Agent Type**  | Multi Agent |
| **Components**  | Tools: Imagen, Gemini, Image Generation/Editing Tools |
| **Vertical**  | Horizontal |

### Agent architecture:  

This diagram shows the detailed architecture of the agents and tools used to implement this workflow.  

<img src="image_renderer_architecture.png" alt="Image Renderer Architecture" width="800"/>  


## Setup and Installation

1.  **Prerequisites**

    *   Python 3.11+
    *   Poetry
        *   For dependency management and packaging. Please follow the
            instructions on the official
            [Poetry website](https://python-poetry.org/docs/) for installation.

        ```bash
        pip install poetry
        ```

    * A project on Google Cloud Platform
    * Google Cloud CLI
        *   For installation, please follow the instruction on the official
            [Google Cloud website](https://cloud.google.com/sdk/docs/install).

2.  **Installation**

    ```bash
    # Clone this repository.
    git clone https://github.com/google/adk-samples.git # Or your fork
    cd adk-samples/python/agents/image-renderer
    # Install the package and dependencies.
    # Note for Linux users: If you get an error related to `keyring` during the installation, you can disable it by running the following command:
    # poetry config keyring.enabled false
    # This is a one-time setup.
    poetry install --with deployment
    ```

3.  **Configuration**

    *   Set up Google Cloud credentials.

        *   There is a `.env-example` file included in the repository. Update this file
            with the values appropriate to your project, and save it as `.env`. The values
            in this file will be read into the environment of your application.

       
    *   Authenticate your GCloud account.

        ```bash
        gcloud auth application-default login
        gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
        ```

## Running the Agent

**Using `adk`**

ADK provides convenient ways to bring up agents locally and interact with them.
Here are some example requests you may ask the Image Renderer Agent to process:

*   `a peaceful mountain landscape at sunset`
*   `a cat riding a bicycle  `

You may talk to the agent using the CLI:

```bash
adk run image_renderer
```

Or on a web interface:

```bash
adk web
```

The command `adk web` will start a web server on your machine and print the URL.
You may open the URL, select "image_renderer" in the top-left drop-down menu, and
a chatbot interface will appear on the right. The conversation is initially
blank. 


## Deployment

The Image Renderer Agent can be deployed to Vertex AI Agent Engine using the following
commands:

```bash
poetry install --with deployment
poetry run python3 deployment/deploy.py --create
```

When the deployment finishes, it will print a line like this:

```
Created remote agent: projects/<PROJECT_NUMBER>/locations/<PROJECT_LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
```

If you forgot the AGENT_ENGINE_ID, you can list existing agents using:

```bash
poetry run python3 deployment/deploy.py --list
```

To test your deployed agent in Agent Engine, you can run the below test deployment test script.
First, replace `<AGENT_ENGINE_ID>` in the .env post the deployment.

```bash
python3 deployment/test_deployment.py
```

To delete the deployed agent, you may run the following command:

```bash
export AGENT_ENGINE_ID=<AGENT_ENGINE_ID>
poetry run python3 deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
```

## Evaluating the Deployment

For running evaluation, install the extra dependencies:

```bash
poetry install --with dev
```

Then the tests and evaluation can be run from the `image_renderer` directory using
the `pytest` module:

```bash
poetry run pytest eval
```

`eval` is a demonstration of how to evaluate the agent, using the
`AgentEvaluator` in ADK. It sends a sample request to the image_renderer agent
and checks if the tool usage is as expected.

## Customization

The Image Renderer Agent can be customized to better suit your requirements. For example:

1.  **Policy Customization:** Modify the policy evaluation criteria to match your specific requirements and standards.
2.  **Image Generation Parameters:** Adjust the Imagen parameters to control image generation quality and characteristics.
3.  **Evaluation Metrics:** Add or modify evaluation metrics to assess different aspects of the generated images.
4.  **Iteration Strategy:** Customize the iteration process to optimize for specific aspects of image quality or policy compliance. 

## Sub-Agents and Workflow

The Image Renderer Agent implements a workflow using the following sub-agents:

1. **Decision Agent**
   * **Primary Responsibility:** Analyzes the user's input (text and images) to determine the appropriate model (`Imagen` or `Gemini`) and the specific `intent`.
   * **Model Criteria:**
       *   **Gemini:** Chosen for real-time interaction, live editing, image fusion, or visual Q&A.
       *   **Imagen:** Chosen for deep customization using reference images for style or subject tuning.
   * **Intent Identification:**
       *   For Imagen: `text_to_image`, `style_customization`, `subject_customization`.
       *   For Gemini: `text_to_image`, `image_edition`, `image_fusion`, `image_QA`.

2. **Image Agent**
   * **Primary Responsibility:** Executes the image-related task based on the model and intent decided by the Decision Agent.
   * It uses the `render_images` tool, which routes the request to the correct model's generation function.
   * **Imagen Functions:** Handles `text_to_image`, `style_customization`, and `subject_customization`.
   * **Gemini Functions:** Handles `text_to_image`, `image_edition` (editing based on a prompt), `image_fusion` (placing one image on another), and `image_QA` (answering questions about an image).
   * Saves generated images to Google Cloud Storage (GCS) and as ADK artifacts.


### Workflow Sequence
1. The workflow begins when the user provides a request (e.g., "create a picture of a cat on a bike" or "place this logo on this t-shirt" with images).
2. The **Decision Agent** is invoked first. It analyzes the request and outputs the `model` and `intent`.
3. The **Image Agent** is then called, receiving the model, intent, and the user's original prompt.
4. The Image Agent's `render_images` tool executes the task using the specified model (Imagen or Gemini) and intent.
5. The resulting image is generated, saved, and returned to the user.

