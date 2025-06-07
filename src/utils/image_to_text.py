import anthropic
import base64

def get_text_from_image(image_path: str) -> str:
    """
    Extracts text of a math question from an image using Anthropic's Claude.

    Args:
        image_path: The file path to the image.

    Returns:
        The extracted text of the question.
    """
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        message = anthropic.Anthropic().messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Given image is having a math question, extract the question along with the options if present. Thats it. Never answer the question. Just extract the question and options. You are providing a OCR service. So dont answer the question. Just extract the question and options."
                        }
                    ],
                }
            ],
        )
        
        if message.content and isinstance(message.content, list) and len(message.content) > 0:
            return message.content[0].text
        else:
            return "Error: Could not extract text from the image."
            
    except Exception as e:
        return f"Error: Failed to process image - {str(e)}"

# Test the function if run directly
if __name__ == '__main__':
    image_path = "img.png"
    result = get_text_from_image(image_path)
    print(result)