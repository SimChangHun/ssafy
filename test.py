import urllib.request

from urllib import parse #인코딩용 임포트

a = "가가다"

e_word = parse.quote(a)

print(e_word)
