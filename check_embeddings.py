
import logging
import os
import tempfile
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_model():
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    
    # Try multiple locations
    cache_dir = None
    possible_dirs = [
        os.path.join(os.path.expanduser("~"), ".cache", "sentence_transformers"),
        os.path.join(tempfile.gettempdir(), "sentence_transformers"),
        os.path.join(os.getcwd(), ".cache", "sentence_transformers")
    ]
    
    logger.info("Checking cache directories...")
    for dir_path in possible_dirs:
        try:
            logger.info(f"Trying: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
            # Test write
            test_file = os.path.join(dir_path, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            cache_dir = dir_path
            logger.info(f"✅ Found writable directory: {cache_dir}")
            break
        except Exception as e:
            logger.warning(f"❌ Failed to write to {dir_path}: {e}")
            continue
            
    if not cache_dir:
        logger.error("Could not find any writable cache directory!")
        return

    try:
        logger.info(f"Loading model {model_name}...")
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        logger.info("✅ Model loaded successfully!")
        
        text = "Hello world"
        embedding = model.encode(text)
        logger.info(f"Generated embedding with shape: {embedding.shape}")
        
        if len(embedding) == 384:
             logger.info("✅ Dimension check passed (384)")
        else:
             logger.error(f"❌ Dimension mismatch. Expected 384, got {len(embedding)}")
             
    except Exception as e:
        logger.error(f"❌ Model loading/encoding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_model()
