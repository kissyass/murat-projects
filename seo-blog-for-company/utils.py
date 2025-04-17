import random
from cryptography.fernet import Fernet

# Encryption Key - This should be stored securely in an environment variable or secure storage
ENCRYPTION_KEY = b'JQu0uhAlauqJA1XDGtniaPlqCLECIGBVAPm6VhYltPc='  # Replace this with a secure key
fernet = Fernet(ENCRYPTION_KEY)
# -------------------------
# Utility Functions for Content Manipulation

def insert_images_evenly(article_text, image_tags):
    """Insert image HTML tags evenly between paragraphs of article_text.
       image_tags should be a list of image tag strings.
    """
    paragraphs = article_text.split("\n\n")
    num_paragraphs = len(paragraphs)
    num_images = len(image_tags)
    if num_images == 0 or num_paragraphs == 0:
        return article_text
    # Determine the interval at which to insert images.
    interval = max(1, num_paragraphs // (num_images + 1))
    new_paragraphs = []
    img_index = 0
    for i, para in enumerate(paragraphs):
        new_paragraphs.append(para)
        if (i + 1) % interval == 0 and img_index < num_images:
            new_paragraphs.append(image_tags[img_index])
            img_index += 1
    return "\n\n".join(new_paragraphs)

def insert_elementor_randomly(article_text, elementor_text):
    """Insert elementor_text randomly in one of the paragraphs of article_text."""
    paragraphs = article_text.split("\n\n")
    if not paragraphs:
        return article_text
    pos = random.randint(0, len(paragraphs)-1)
    paragraphs.insert(pos, elementor_text)
    return "\n\n".join(paragraphs)

# Encrypt a password
def encrypt_password(plaintext_password):
    return fernet.encrypt(plaintext_password.encode()).decode()

# Decrypt a password
def decrypt_password(encrypted_password):
    return fernet.decrypt(encrypted_password.encode()).decode()
