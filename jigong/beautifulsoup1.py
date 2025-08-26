from bs4 import BeautifulSoup

with open("books.xml", "r", encoding = "utf8")as books_file:
    books_xml= books_file.read()       # 파일을문자열로읽어오기

soup = BeautifulSoup(books_xml, "lxml") # lxml파서를사용해데이터분석

for book_info in soup.find_all("publisher"):

    print(book_info)
    print(book_info.get_text())     

