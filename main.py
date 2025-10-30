import requests
from typing import List, Dict, Optional
from datetime import datetime
import json


class GitHubAPIConsumer:
    """Classe para consumir a API do GitHub com ordenação e tratamento de dados"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa o consumidor da API
        
        Args:
            token: Token de autenticação do GitHub (opcional, mas recomendado para evitar rate limit)
        """
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-API-Consumer"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Realiza requisição à API com tratamento de erros
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da query
            
        Returns:
            Dados da resposta em formato JSON
        """
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"Recurso não encontrado: {endpoint}")
            elif response.status_code == 403:
                raise ValueError("Rate limit excedido. Use um token de autenticação.")
            elif response.status_code == 401:
                raise ValueError("Token de autenticação inválido")
            else:
                raise ValueError(f"Erro HTTP {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Erro na requisição: {e}")
    
    def get_users(self, since: int = 0, per_page: int = 30) -> List[Dict]:
        """
        Lista usuários do GitHub
        
        Args:
            since: ID do usuário a partir do qual começar a listagem
            per_page: Quantidade de resultados por página (max 100)
            
        Returns:
            Lista de usuários
        """
        params = {"since": since, "per_page": min(per_page, 100)}
        users = self._make_request("/users", params)
        return self._treat_users_data(users)
    
    def search_users(self, query: str, sort: str = "best-match", 
                     order: str = "desc", per_page: int = 30) -> Dict:
        """
        Busca usuários com ordenação
        
        Args:
            query: Termo de busca
            sort: Campo de ordenação (followers, repositories, joined, best-match)
            order: Ordem (asc ou desc)
            per_page: Quantidade de resultados
            
        Returns:
            Dicionário com resultados e metadados
        """
        valid_sorts = ["followers", "repositories", "joined", "best-match"]
        if sort not in valid_sorts:
            raise ValueError(f"Sort inválido. Use: {', '.join(valid_sorts)}")
        
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100)
        }
        
        result = self._make_request("/search/users", params)
        return {
            "total_count": result.get("total_count", 0),
            "incomplete_results": result.get("incomplete_results", False),
            "users": self._treat_users_data(result.get("items", []))
        }
    
    def get_user_details(self, username: str) -> Dict:
        """
        Obtém detalhes de um usuário específico
        
        Args:
            username: Nome de usuário do GitHub
            
        Returns:
            Dados tratados do usuário
        """
        user = self._make_request(f"/users/{username}")
        return self._treat_user_detail(user)
    
    def search_repositories(self, query: str, sort: str = "best-match",
                           order: str = "desc", per_page: int = 30) -> Dict:
        """
        Busca repositórios com ordenação
        
        Args:
            query: Termo de busca
            sort: Campo de ordenação (stars, forks, help-wanted-issues, updated)
            order: Ordem (asc ou desc)
            per_page: Quantidade de resultados
            
        Returns:
            Dicionário com resultados e metadados
        """
        valid_sorts = ["stars", "forks", "help-wanted-issues", "updated", "best-match"]
        if sort not in valid_sorts:
            raise ValueError(f"Sort inválido. Use: {', '.join(valid_sorts)}")
        
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100)
        }
        
        result = self._make_request("/search/repositories", params)
        return {
            "total_count": result.get("total_count", 0),
            "incomplete_results": result.get("incomplete_results", False),
            "repositories": self._treat_repositories_data(result.get("items", []))
        }
    
    def _treat_users_data(self, users: List[Dict]) -> List[Dict]:
        """Trata dados de lista de usuários"""
        treated = []
        for user in users:
            treated.append({
                "id": user.get("id"),
                "login": user.get("login"),
                "avatar_url": user.get("avatar_url"),
                "url": user.get("html_url"),
                "type": user.get("type"),
                "site_admin": user.get("site_admin", False)
            })
        return treated
    
    def _treat_user_detail(self, user: Dict) -> Dict:
        """Trata dados detalhados de um usuário"""
        created_at = user.get("created_at")
        if created_at:
            created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            created_at = created_at.strftime("%d/%m/%Y %H:%M:%S")
        
        updated_at = user.get("updated_at")
        if updated_at:
            updated_at = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
            updated_at = updated_at.strftime("%d/%m/%Y %H:%M:%S")
        
        return {
            "id": user.get("id"),
            "login": user.get("login"),
            "name": user.get("name"),
            "company": user.get("company"),
            "blog": user.get("blog"),
            "location": user.get("location"),
            "email": user.get("email"),
            "bio": user.get("bio"),
            "public_repos": user.get("public_repos", 0),
            "public_gists": user.get("public_gists", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "created_at": created_at,
            "updated_at": updated_at,
            "avatar_url": user.get("avatar_url"),
            "url": user.get("html_url")
        }
    
    def _treat_repositories_data(self, repos: List[Dict]) -> List[Dict]:
        """Trata dados de repositórios"""
        treated = []
        for repo in repos:
            created_at = repo.get("created_at")
            if created_at:
                created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                created_at = created_at.strftime("%d/%m/%Y %H:%M:%S")
            
            updated_at = repo.get("updated_at")
            if updated_at:
                updated_at = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                updated_at = updated_at.strftime("%d/%m/%Y %H:%M:%S")
            
            treated.append({
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "owner": repo.get("owner", {}).get("login"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "created_at": created_at,
                "updated_at": updated_at,
                "url": repo.get("html_url"),
                "is_fork": repo.get("fork", False),
                "is_archived": repo.get("archived", False)
            })
        return treated


def main():
    """Exemplo de uso da classe"""
    
    # Inicializar sem token (com rate limit de 60 req/hora)
    # Para uso com token: api = GitHubAPIConsumer(token="seu_token_aqui")
    api = GitHubAPIConsumer()
    
    print("=" * 80)
    print("EXEMPLO 1: Buscar usuários por seguidores (ordenação decrescente)")
    print("=" * 80)
    try:
        result = api.search_users(
            query="location:brazil",
            sort="followers",
            order="desc",
            per_page=5
        )
        print(f"\nTotal de resultados: {result['total_count']}")
        print(f"\nTop 5 usuários do Brasil por seguidores:\n")
        for i, user in enumerate(result['users'], 1):
            print(f"{i}. {user['login']}")
            print(f"   URL: {user['url']}")
            print()
    except ValueError as e:
        print(f"Erro: {e}")
    
    print("=" * 80)
    print("EXEMPLO 2: Buscar repositórios Python por stars")
    print("=" * 80)
    try:
        result = api.search_repositories(
            query="language:python",
            sort="stars",
            order="desc",
            per_page=5
        )
        print(f"\nTotal de resultados: {result['total_count']}")
        print(f"\nTop 5 repositórios Python por stars:\n")
        for i, repo in enumerate(result['repositories'], 1):
            print(f"{i}. {repo['full_name']}")
            print(f"   Descrição: {repo['description']}")
            print(f"   Stars: {repo['stars']:,} | Forks: {repo['forks']:,}")
            print(f"   URL: {repo['url']}")
            print()
    except ValueError as e:
        print(f"Erro: {e}")
    
    print("=" * 80)
    print("EXEMPLO 3: Detalhes de um usuário específico")
    print("=" * 80)
    try:
        user = api.get_user_details("torvalds")
        print(f"\nDetalhes de {user['login']}:\n")
        print(f"Nome: {user['name']}")
        print(f"Localização: {user['location']}")
        print(f"Bio: {user['bio']}")
        print(f"Repositórios públicos: {user['public_repos']}")
        print(f"Seguidores: {user['followers']:,}")
        print(f"Seguindo: {user['following']}")
        print(f"Criado em: {user['created_at']}")
        print(f"URL: {user['url']}")
    except ValueError as e:
        print(f"Erro: {e}")
    
    print("\n" + "=" * 80)
    print("EXEMPLO 4: Exportar dados para JSON")
    print("=" * 80)
    try:
        result = api.search_repositories(
            query="machine-learning",
            sort="updated",
            order="desc",
            per_page=3
        )
        
        filename = "github_repos.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nDados exportados para {filename}")
    except ValueError as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()