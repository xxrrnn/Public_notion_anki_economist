import re
from PIL import Image
with open("../words_repeat.txt","r",encoding="utf-8") as file:
    a = file.readlines()
print(len(a))