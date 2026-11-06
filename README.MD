# GeoDocker Challenge — Mapeamento Colaborativo Urbano

Aplicação web de mapeamento colaborativo de ocorrências urbanas (buracos, alagamentos, lixo, falhas de iluminação e acessibilidade), orquestrada via Docker Compose com persistência de dados e imagens.

---
## Menbros
   Brenno Yasuhei
   Ronald Bruno
   André Felipe

## 1. Arquitetura e Estrutura do Sistema

A solução está dividida em microsserviços isolados que comunicam numa rede interna Docker:

- **Frontend**: Servidor Nginx com interface HTML5/JS e mapa interativo (Leaflet + OpenStreetMap).
- **Backend**: API REST desenvolvida em Python (FastAPI) para gestão das operações CRUD e integração com o armazenamento S3.
- **Banco de Dados**: PostgreSQL 15 num contentor com volume dedicado.
- **Armazenamento de Imagens**: MinIO (serviço independente compatível com S3) com volume próprio para manter as fotografias.
- **Orquestração**: Docker Compose a interligar os serviços através da rede `geonet`.

### Mapeamento de Portas
- `8080:80` — **Frontend**: Interface web do utilizador.
- `8000:8000` — **Backend**: API REST e Swagger Docs (`http://localhost:8000/docs`).
- `9000:9000` — **MinIO API**: Leitura e carregamento de imagens via protocolo S3.
- `9001:9001` — **MinIO Console**: Painel de administração do storage.

---

## 2. Desafios DevOps Obrigatórios (Passo a Passo e Comandos)

### Desafio A: Inicialização Automatizada
> **Requisito**: Arrancar toda a infraestrutura com um único comando sem instalar dependências manualmente no host.

**Comando:**
```bash
docker compose up -d --build

Execute o comando acima na raiz do repositório
Abra o navegador no endereço http://localhost:8080

### Desafio B: Persistência dos Dados (PostgreSQL)
Requisito: Cadastrar pelo menos 5 ocorrências, interromper/remover os contêineres e demonstrar que os registros e coordenadas continuam disponíveis.
1.Acesse http://localhost:8080 e cadastre no mínimo 5 ocorrências clicando em pontos diferentes do mapa e preenchendo o formulário com foto.
2.Pare e remova completamente os contêineres em execução:
  docker compose down
3.Suba novamente toda a infraestrutura:
docker compose up -d
4.Atualize a página do navegador

### Desafio C: Persistência das Imagens (MinIO / S3)
Requisito: Demonstrar que as fotografias associadas às ocorrências continuam acessíveis após remover e recriar os contêineres.
1.Clique em qualquer marcador no mapa e abra a imagem da ocorrência em uma nova aba do navegador.
2.Copie e salve o link da fotografia (exemplo: http://localhost:9000/ocorrencias/...).
3.Execute o comando para destruir e recriar os contêineres:
docker compose down
docker compose up -d
4.Recarregue a URL da imagem ou atualize a página principal do mapa. A foto continuará acessível sem erros 404.

### Desafio D: Diagnóstico e Comunicação entre Serviços
Requisito: Exibir o estado dos serviços, inspecionar logs de comunicação e explicar como os serviços se comunicam por nomes de rede no Docker[cite: 1].
1. Comando para verificar o estado dos contêineres:
docker compose ps
2. Comandos para inspeção de logs:
# Visualizar logs de toda a aplicação
docker compose logs

# Visualizar logs em tempo real apenas da API Backend
docker compose logs -f backend

# Visualizar logs da base de dados PostgreSQL
docker compose logs db

3. Explicação técnica da comunicação entre serviços:
Todos os contêineres são conectados à rede do tipo bridge chamada geonet[cite: 1]. O Docker Compose provê um servidor DNS embutido nessa rede que resolve automaticamente o nome do serviço definido no docker-compose.yml para o endereço IP interno do contêiner[cite: 1].

Comunicação Backend -> Banco de Dados: A API conecta-se ao PostgreSQL usando a URL postgresql://geo_user:geo_pass@db:5432/geo_db. O host db é resolvido internamente pelo Docker para o IP do contêiner do PostgreSQL[cite: 1].

Comunicação Backend -> Storage: O upload das fotografias é feito enviando as requisições S3 para http://storage:9000. O nome storage é resolvido para o IP do contêiner do MinIO[cite: 1].

             Ação	                                     Comando
Construir e iniciar os contêineres	           docker compose up -d --build[cite: 1]

Parar e remover os contêineres	               docker compose down[cite: 1]

Verificar o status dos contêineres	           docker compose ps[cite: 1]

Inspecionar logs de todos os serviços	       docker compose logs[cite: 1]

Acompanhar logs em tempo real	               docker compose logs -f[cite: 1]

XXX. Exportar as imagens Docker compiladas em um arquivo .tar
docker save -o imagens_geodocker.tar geodocker-frontend geodocker-backend postgres:15-alpine minio/minio
---