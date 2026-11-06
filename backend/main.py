import os
import boto3
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid

# --- 1. CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE ---
DATABASE_URL = os.getenv("DATABASE_URL")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "storage:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "ocorrencias")

# --- 2. CONFIGURAÇÃO DA BASE DE DADOS (PostgreSQL / SQLAlchemy) ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Dados da Ocorrência
class Ocorrencia(Base):
    __tablename__ = "ocorrencias"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    descricao = Column(String)
    categoria = Column(String)
    status = Column(String, default="Pendente") # Campo de estado/prioridade
    lat = Column(Float) # Coordenada Latitude
    lng = Column(Float) # Coordenada Longitude
    imagem_url = Column(String) # URL pública da foto no MinIO

# Cria as tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)

# --- 3. INICIALIZAÇÃO DA APLICAÇÃO E CORS ---
app = FastAPI()

# Permite chamadas do Frontend (evita bloqueios de CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. CONEXÃO AO MINIO (S3) ---
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{S3_ENDPOINT}",
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# Garante a criação do bucket e torna a leitura pública
try:
    s3_client.create_bucket(Bucket=S3_BUCKET)
    policy = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::%s/*"]}]}' % S3_BUCKET
    s3_client.put_bucket_policy(Bucket=S3_BUCKET, Policy=policy)
except:
    pass

# Função de injeção de dependência da BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. ENDPOINTS DA API (OPERÇÕES CRUD) ---

# CREATE: Registar nova ocorrência com upload de imagem
@app.post("/ocorrencias/")
async def criar_ocorrencia(
    titulo: str = Form(...), 
    descricao: str = Form(...), 
    categoria: str = Form(...),
    status: str = Form(...), 
    lat: float = Form(...), 
    lng: float = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Gera um nome único para a imagem
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    
    # Upload para o serviço MinIO
    s3_client.upload_fileobj(file.file, S3_BUCKET, file_name)
    imagem_url = f"http://localhost:9000/{S3_BUCKET}/{file_name}"
    
    # Grava na base de dados
    nova_ocorrencia = Ocorrencia(
        titulo=titulo, 
        descricao=descricao, 
        categoria=categoria, 
        status=status, 
        lat=lat, 
        lng=lng, 
        imagem_url=imagem_url
    )
    db.add(nova_ocorrencia)
    db.commit()
    db.refresh(nova_ocorrencia)
    return nova_ocorrencia

# READ: Listar todas as ocorrências
@app.get("/ocorrencias/")
def listar_ocorrencias(db: Session = Depends(get_db)):
    return db.query(Ocorrencia).all()

# UPDATE: Editar ocorrência (alterar título, descrição, categoria ou status)
@app.put("/ocorrencias/{id}")
def atualizar_ocorrencia(
    id: int, 
    titulo: str = Form(None), 
    descricao: str = Form(None), 
    categoria: str = Form(None), 
    status: str = Form(None), 
    db: Session = Depends(get_db)
):
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == id).first()
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    if titulo: ocorrencia.titulo = titulo
    if descricao: ocorrencia.descricao = descricao
    if categoria: ocorrencia.categoria = categoria
    if status: ocorrencia.status = status
    
    db.commit()
    return ocorrencia

# DELETE: Eliminar ocorrência
@app.delete("/ocorrencias/{id}")
def deletar_ocorrencia(id: int, db: Session = Depends(get_db)):
    ocorrencia = db.query(Ocorrencia).filter(Ocorrencia.id == id).first()
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    db.delete(ocorrencia)
    db.commit()
    return {"status": "sucesso"}