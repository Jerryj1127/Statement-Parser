from common.config import ConfigCommon

class Config(ConfigCommon):
    card_no_pattern = r'\b\d{4}[\s\w*]{6,12}\d{4}\b'
