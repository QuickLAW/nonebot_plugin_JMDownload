
from PIL.ImageFile import ImageFile


from PIL.ImageFile import ImageFile


from PIL import Image

def load_img(path) -> ImageFile:
    with Image.open(str(path)) as img:
        img.verify()  # 验证图片完整性
        img.load()  # 加载像素数据
    return img

if __name__ == '__main__':
    path = r"C:\Users\Elysia\Desktop\Code\Python\QQbotDevelop\data\nonebot_plugin_jmdownload\downloads\32D阿西 11-12月福利\1\00001.jpg"
    load_img(path)