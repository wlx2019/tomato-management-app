import os
import json
import logging

CONFIG_FILE = 'config.json'
EXCEL_OUTPUT_DIR = '结算单'

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_file):
            default_config = {
                "company_name": "XX农业有限公司", "phone_number": "000-0000-0000",
                "footer_text": "本结算单仅供内部参考，最终结算以实际为准。", "excel_output_dir": EXCEL_OUTPUT_DIR
            }
            self.set_all(default_config)
            return default_config
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            return self._load_config()

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self._save_config()
    
    def set_all(self, config_dict):
        self.config = config_dict
        self._save_config()

    def _save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logging.error(f"保存配置文件失败: {e}")