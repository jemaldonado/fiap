import csv
import logging
import os
import re
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("books_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BooksScraper")


class BooksScraper:
    """
    Classe responsável por extrair dados de livros do site Books to Scrape.
    
    Esta classe fornece métodos para extrair categorias, navegar pelas páginas
    de cada categoria e coletar informações detalhadas de cada livro.
    
    Attributes:
        base_url (str): URL base do site Books to Scrape.
        session (requests.Session): Sessão HTTP para fazer requisições.
        categories (List[Dict]): Lista de categorias extraídas.
        books (List[Dict]): Lista de livros extraídos com todos os detalhes.
        extract_detailed_info (bool): Se True, extrai informações detalhadas
            das páginas individuais de cada livro.
    """
    
    def __init__(self, extract_detailed_info: bool = True) -> None:
        """
        Inicializa o scraper com valores padrão.
        
        Args:
            extract_detailed_info: Se True, o scraper extrairá informações
                detalhadas das páginas individuais de cada livro.
        """
        self.base_url = "https://books.toscrape.com/"
        self.session = requests.Session()
        
        # Adiciona um User-Agent para simular um navegador comum
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.categories = []
        self.books = []
        self.extract_detailed_info = extract_detailed_info
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Retorna um objeto BeautifulSoup para a URL fornecida.
        
        Args:
            url: URL da página a ser analisada.
            
        Returns:
            BeautifulSoup: Objeto BeautifulSoup da página ou None se ocorrer erro.
            
        Raises:
            requests.exceptions.RequestException: Se houver problemas na requisição HTTP.
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar {url}: {e}")
            return None
    
    def extract_categories(self) -> List[Dict[str, str]]:
        """
        Extrai todas as categorias disponíveis no site.
        
        Navega pela página inicial e extrai o nome e URL de cada categoria
        listada no menu lateral.
        
        Returns:
            List[Dict[str, str]]: Lista de dicionários contendo nome e URL de cada categoria.
                Cada dicionário tem as chaves 'name' e 'url'.
        """
        logger.info("Extraindo categorias...")
        soup = self.get_soup(self.base_url)
        
        if not soup:
            logger.error("Não foi possível obter a página inicial")
            return []
        
        # Localiza o menu lateral de categorias
        category_container = soup.select_one('div.side_categories > ul.nav > li > ul')
        
        if not category_container:
            logger.error("Não foi possível encontrar o menu de categorias")
            return []
        
        # Limpa a lista de categorias para evitar duplicações em execuções repetidas
        self.categories = []
        
        # Extrai os links de categoria
        for category_item in category_container.find_all('li'):
            link_tag = category_item.find('a')
            if link_tag:
                category_name = link_tag.text.strip()
                category_url = urljoin(self.base_url, link_tag['href'])
                self.categories.append({
                    'name': category_name,
                    'url': category_url
                })
        
        logger.info(f"Total de categorias encontradas: {len(self.categories)}")
        return self.categories
    
    def extract_rating(self, star_element) -> int:
        """
        Converte a classificação em estrelas para um valor numérico.
        
        Args:
            star_element: Elemento HTML que contém a classificação em estrelas.
            
        Returns:
            int: Classificação numérica de 1 a 5, ou 0 se não for possível extrair.
        """
        if not star_element:
            print("sem star_element")
            return 0
        
        # Obtém as classes do elemento
        classes = star_element.get('class', [])

        # Procura pela classe que indica a classificação de estrelas       
        if 'star-rating' in classes:
            # A parte da classificação é a última palavra na classe 
            rating_value = classes[-1]  # Ex: 'Four'
            return {
                'One': 1,
                'Two': 2,
                'Three': 3,
                'Four': 4,
                'Five': 5
            }.get(rating_value, 0)  # Retorna valor correspondente ou 0 se não encontrado
        
        return 0  # Se não encontrou classificação


    def extract_book_details(self, book_url: str) -> Dict[str, Union[str, int, float]]:
        """
        Extrai detalhes adicionais de uma página individual de livro.

        Args:
            book_url: URL da página detalhada do livro.

        Returns:
            Dict[str, Union[str, int, float]]: Dicionário com os detalhes completos do livro.
        """
        soup = self.get_soup(book_url)

        if not soup:
            logger.error(f"Não foi possível obter a página de detalhes: {book_url}")
            return {}

        # Dicionário para armazenar todos os detalhes do livro
        book_details = {}

        try:
            # Extrai o título
            title_element = soup.select_one('div.product_main h1')
            if title_element:
                book_details['title'] = title_element.text.strip()

            # Extrai a descrição do produto
            product_description = soup.select_one('#product_description ~ p')
            book_details['description'] = product_description.text.strip() if product_description else "Sem descrição"

            # Extrai informações da tabela de detalhes
            info_table = soup.select_one('table.table-striped')
            if info_table:
                rows = info_table.select('tr')
                for row in rows:
                    header = row.select_one('th').text.strip()
                    value = row.select_one('td').text.strip()

                    # Mapeamento para chaves padronizadas
                    header_mapping = {
                        'UPC': 'upc',
                        'Product Type': 'product_type',
                        'Price (excl. tax)': 'price_excl_tax',
                        'Price (incl. tax)': 'price_incl_tax',
                        'Tax': 'tax',
                        'Availability': 'availability',
                        'Number of reviews': 'number_of_reviews'
                    }

                    if header in header_mapping:
                        key = header_mapping[header]
                        if key in ['price_excl_tax', 'price_incl_tax', 'tax']:
                            book_details[key] = float(value.replace('£', ''))  # Converte para float
                        elif key == 'number_of_reviews':
                            book_details[key] = int(value)  # Captura o número de avaliações
                        else:
                            book_details[key] = value

            # URL da imagem em alta resolução
            image_div = soup.select_one('#product_gallery img')
            if image_div:
                relative_image_url = image_div.get('src')
                book_details['image_url'] = urljoin(self.base_url, relative_image_url)

            # Extrai a classificação (rating)
            rating_element = soup.select_one('p.star-rating')
            if rating_element:
                book_details['rating'] = self.extract_rating(rating_element)
            else:
                logger.warning(f"Rating não encontrado para o livro {book_url}")
                book_details['rating'] = 0

        except Exception as e:
            logger.error(f"Erro ao extrair detalhes do livro {book_url}: {e}", exc_info=True)

        return book_details
        
    
    def extract_books_from_page(self, url: str, category_name: str) -> List[Dict[str, Union[str, int, float]]]:
        """
        Extrai todos os livros de uma página específica.
        
        Args:
            url: URL da página.
            category_name: Nome da categoria dos livros.
            
        Returns:
            List[Dict[str, Union[str, int, float]]]: Lista de livros extraídos da página,
                cada livro representado como um dicionário de atributos.
        """
        page_books = []
        soup = self.get_soup(url)
        
        if not soup:
            logger.error(f"Falha ao obter a página {url}")
            return []
        
        book_containers = soup.select('article.product_pod')
        
        for book in book_containers:
            try:
                # Extrai o título
                title_element = book.select_one('h3 > a')
                title = title_element.get('title', '').strip() if title_element else 'Sem título'
                
                # URL do livro para detalhes adicionais
                book_url = urljoin(url, title_element.get('href')) if title_element else None
                
                # Obtém informações básicas da página de listagem
                basic_info = {
                    'title': title,
                    'book_url': book_url,
                    'category': category_name
                }
                
                # Extrai o preço
                price_element = book.select_one('div.product_price p.price_color')
                if price_element:
                    basic_info['price'] = price_element.text.strip()
                
                # Extrai a classificação (rating)
                rating_element = book.select_one('p.star-rating')
                if rating_element:
                    basic_info['rating'] = self.extract_rating(rating_element)
                
                # Visita a página de detalhes do livro para extrair mais informações
                if book_url:
                    logger.debug(f"Extraindo detalhes do livro: {title}")
                    detailed_info = self.extract_book_details(book_url)
                    
                    # Combina as informações básicas com os detalhes
                    book_info = {**basic_info, **detailed_info}
                    
                    page_books.append(book_info)
                    
                    # Pausa breve entre requisições de páginas de detalhes
                    time.sleep(0.2)
            
            except Exception as e:
                logger.warning(f"Erro ao extrair livro: {e}")
        
        return page_books
    
    def extract_books_from_category(self, category: Dict[str, str]) -> List[Dict[str, Union[str, int, float]]]:
        """
        Extrai todos os livros de uma categoria, incluindo paginação.
        
        Args:
            category: Dicionário contendo nome e URL da categoria.
            
        Returns:
            List[Dict[str, Union[str, int, float]]]: Lista de livros extraídos da categoria.
        """
        logger.info(f"Extraindo livros da categoria: {category['name']}...")
        category_books = []
        page_url = category['url']
        page_num = 1
        
        while True:
            logger.info(f"  Processando página {page_num} da categoria {category['name']}...")
            page_books = self.extract_books_from_page(page_url, category['name'])
            
            if not page_books:
                logger.warning(f"  Não foram encontrados livros na página {page_num} da categoria {category['name']}")
                break
                
            category_books.extend(page_books)
            
            # Verifica se existe próxima página
            soup = self.get_soup(page_url)
            if not soup:
                break
                
            next_button = soup.select_one('li.next > a')
            
            if not next_button:
                logger.info(f"  Última página da categoria {category['name']} alcançada")
                break
                
            # Atualiza a URL para a próxima página
            page_url = urljoin(page_url, next_button['href'])
            page_num += 1
            
            # Pausa breve para evitar sobrecarregar o servidor
            time.sleep(0.5)
        
        logger.info(f"  Encontrados {len(category_books)} livros na categoria {category['name']}")
        return category_books
    
    def scrape_all_books(self) -> List[Dict[str, Union[str, int, float]]]:
        """
        Extrai todos os livros de todas as categorias.
        
        Este método coordena o processo completo de extração, primeiro obtendo
        todas as categorias e depois extraindo livros de cada uma delas.
        
        Returns:
            List[Dict[str, Union[str, int, float]]]: Lista com todos os livros do site.
        """
        logger.info("Iniciando extração de todos os livros...")
        
        # Primeiro obtém todas as categorias
        self.extract_categories()
        
        # Limpa a lista de livros para evitar duplicações em execuções repetidas
        self.books = []
        
        # Em seguida, extrai os livros de cada categoria
        for i, category in enumerate(self.categories, 1):
            logger.info(f"Processando categoria {i}/{len(self.categories)}: {category['name']}")
            category_books = self.extract_books_from_category(category)
            self.books.extend(category_books)
            
            # Pausa entre categorias para não sobrecarregar o servidor
            if i < len(self.categories):
                time.sleep(1)
        
        logger.info(f"Extração concluída! Total de livros extraídos: {len(self.books)}")
        return self.books
    
    def save_to_csv(self, filename: str = "books.csv") -> None:
        """
        Salva os livros extraídos em um arquivo CSV.
        
        Args:
            filename: Nome do arquivo CSV de saída.
                
        Raises:
            IOError: Se houver problemas ao escrever o arquivo.
        """
        if not self.books:
            logger.warning("Nenhum livro para salvar. Execute scrape_all_books() primeiro.")
            return
        
        try:
            # Define os campos que serão exportados, priorizando campos detalhados se disponíveis
            all_fields = set()
            for book in self.books:
                all_fields.update(book.keys())
            
            # Ordena os campos para ter uma ordem consistente
            fieldnames = sorted(list(all_fields))
            
            # Prioriza campos importantes no início do CSV
            priority_fields = [
                'title', 'category', 'price', 'price_excl_tax', 'price_incl_tax', 
                'rating', 'upc', 'availability', 'availability_detail', 'stock_quantity',
                'description', 'image_url', 'book_url'
            ]
            
            # Move os campos prioritários para o início
            for field in reversed(priority_fields):
                if field in fieldnames:
                    fieldnames.remove(field)
                    fieldnames.insert(0, field)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for book in self.books:
                    writer.writerow(book)
                
            logger.info(f"Dados salvos com sucesso em {filename}")
        except Exception as e:
            logger.error(f"Erro ao salvar o arquivo CSV: {e}")
            raise


def main() -> None:
    """
    Função principal que executa o processo completo de web scraping.
    
    Permite configurar o modo de execução e o nome do arquivo de saída através
    de argumentos de linha de comando.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Web Scraper para Books to Scrape')
    parser.add_argument('--simple', action='store_true', 
                        help='Extrai apenas informações básicas (mais rápido)')
    parser.add_argument('--output', type=str, default='books.csv',
                        help='Nome do arquivo CSV de saída')
    args = parser.parse_args()
    
    try:
        logger.info("Iniciando o sistema de web scraping para Books to Scrape...")
        
        # Cria o scraper com configuração baseada nos argumentos
        extract_detailed = not args.simple
        scraper = BooksScraper(extract_detailed_info=extract_detailed)
        
        if extract_detailed:
            logger.info("Modo detalhado: extraindo informações completas de cada livro (pode ser lento)")
        else:
            logger.info("Modo simples: extraindo apenas informações básicas de cada livro")
        
        # Executa o scraping e salva os resultados
        scraper.scrape_all_books()
        scraper.save_to_csv(args.output)
        
        logger.info(f"Web scraping concluído com sucesso! Resultados salvos em {args.output}")
    except Exception as e:
        logger.critical(f"Erro crítico durante a execução: {e}", exc_info=True)
        raise


# Execução do script
if __name__ == "__main__":
    main()