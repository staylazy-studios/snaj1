from setuptools import setup

setup(
        name = "snaj (not ready for production)",
        options = {
            "build_apps": {
                "include_patterns": [
                    "assets/**/*",
                    "*.txt"
                ],
                "gui_apps": {
                    "snaj (not ready for production)": "main.py"
                },
                "plugins": [
                    "pandagl",
                    "p3openal_audio"
                ],
                "log_filename": "$USER_APPDATA/snaj/output.log",
                "log_append": False
            }
        }
)
