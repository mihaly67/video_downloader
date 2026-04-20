from bs4 import BeautifulSoup

with open('test-videos.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', href=True)
for link in links:
    print(f"{link.text.strip()} -> {link['href']}")
