import os
import platform
import shutil


# =========================================================
# SYSTEM INFORMATION
# =========================================================

def get_system_info():
    """
    Return basic information about the computer.
    """

    try:

        total, used, free = shutil.disk_usage(
            os.path.abspath(
                os.sep
            )
        )

        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        free_gb = free / (1024 ** 3)

        return (
            "SYSTEM INFORMATION\n\n"
            f"Computer: {platform.node()}\n"
            f"Operating system: {platform.system()} "
            f"{platform.release()}\n"
            f"Architecture: {platform.machine()}\n"
            f"Processor: {platform.processor()}\n"
            f"Python: {platform.python_version()}\n"
            f"Disk total: {total_gb:.1f} GB\n"
            f"Disk used: {used_gb:.1f} GB\n"
            f"Disk free: {free_gb:.1f} GB"
        )

    except Exception as error:

        return (
            "I couldn't retrieve system information, Sir. "
            f"{error}"
        )