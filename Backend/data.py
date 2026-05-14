from __future__ import annotations


CATEGORY_LABELS = {
    "acessorios": "Pontos de apoio",
    "face": "Cobertura segura",
    "labios": "Sinal suave",
    "olhos": "Olhar atento",
    "skincare": "Camada calma",
    "kits": "Planos discretos",
}


PRODUCTS = [
    {
        "id": "corretivo-4-seasons",
        "nome": "Corretivo Colorido | Sinais Leves",
        "categoria": "face",
        "linha": "maquiagem",
        "descricao": "Alta cobertura para suavizar sinais recentes e devolver um acabamento tranquilo, sem chamar atencao.",
        "preco": "R$ 59,90",
        "parcelamento": "ou em 2x de R$ 29,95",
        "imagem": "img/img-produtos-corretivos-makemana.jpg",
        "destaque": True,
    },
    {
        "id": "base-second-skin",
        "nome": "Base Liquida Fluid | Segunda Pele",
        "categoria": "face",
        "linha": "maquiagem",
        "descricao": "Textura leve para criar uma camada firme entre voce e o mundo, com cobertura que acompanha o dia.",
        "preco": "R$ 98,90",
        "parcelamento": "ou em 2x de R$ 49,45",
        "imagem": "img/img-produtos-base-makemana.jpg",
        "destaque": True,
    },
    {
        "id": "paleta-behind-scenes",
        "nome": "Paleta de Sombras | Bastidores",
        "categoria": "olhos",
        "linha": "maquiagem",
        "descricao": "Doze tons para ler o ambiente, mudar de plano com delicadeza e manter tudo no seu ritmo.",
        "preco": "R$ 119,90",
        "parcelamento": "ou em 3x de R$ 39,97",
        "imagem": "img/img-produtos-paletaDeSombra-makemana.jpg",
        "destaque": True,
    },
    {
        "id": "mascara-speak-volume",
        "nome": "Mascara de Cilios | Olhar Firme",
        "categoria": "olhos",
        "linha": "maquiagem",
        "descricao": "Definicao resistente para quando o olhar precisa dizer mais do que a boca pode mostrar.",
        "preco": "R$ 64,90",
        "parcelamento": "ou em 2x de R$ 32,45",
        "imagem": "img/img-produtos-rimel-makemana.jpg",
        "destaque": True,
    },
    {
        "id": "hidratante-safe-skin",
        "nome": "Hidratante Calmante | Pele em Paz",
        "categoria": "skincare",
        "linha": "skincare",
        "descricao": "Hidratacao prolongada para acalmar a superficie e reforcar a barreira quando tudo parece sensivel.",
        "preco": "R$ 74,90",
        "parcelamento": "ou em 2x de R$ 37,45",
        "imagem": "img/img-categorias-skincare-makemana.jpg",
        "destaque": False,
    },
    {
        "id": "serum-renova",
        "nome": "Serum Facial | Recalcula",
        "categoria": "skincare",
        "linha": "skincare",
        "descricao": "Formula leve para recuperar o brilho aos poucos e lembrar que sempre existe uma nova rota.",
        "preco": "R$ 89,90",
        "parcelamento": "ou em 3x de R$ 29,97",
        "imagem": "img/img-produtos-makemana.jpg",
        "destaque": False,
    },
    {
        "id": "kit-recomeco",
        "nome": "Kit Recomeco | Primeiro Passo",
        "categoria": "kits",
        "linha": "kits",
        "descricao": "Base, corretivo e mascara em uma combinacao discreta para recompor, observar e seguir com firmeza.",
        "preco": "R$ 199,90",
        "parcelamento": "ou em 4x de R$ 49,98",
        "imagem": "img/img-produtos-base-makemana.jpg",
        "destaque": False,
    },
    {
        "id": "kit-essencial",
        "nome": "Kit Essencial | Camada de Apoio",
        "categoria": "kits",
        "linha": "kits",
        "descricao": "Hidratante, serum e protetor em uma rotina silenciosa para fortalecer a pele antes de sair.",
        "preco": "R$ 169,90",
        "parcelamento": "ou em 4x de R$ 42,48",
        "imagem": "img/img-categorias-skincare-makemana.jpg",
        "destaque": False,
    },
    {
        "id": "pinceis-controle",
        "nome": "Kit de Pinceis | Mao Firme",
        "categoria": "acessorios",
        "linha": "kits",
        "descricao": "Cinco pinceis para aplicar cada camada com precisao, sem pressa e sem perder o controle.",
        "preco": "R$ 84,90",
        "parcelamento": "ou em 2x de R$ 42,45",
        "imagem": "img/img-categorias-acessorios-makemana.jpg",
        "destaque": False,
    },
    {
        "id": "batom-presenca",
        "nome": "Batom Cremoso | Palavra Baixa",
        "categoria": "labios",
        "linha": "maquiagem",
        "descricao": "Cor confortavel para marcar presenca com discricao, mesmo quando e melhor falar pouco.",
        "preco": "R$ 42,90",
        "parcelamento": "ou em 2x de R$ 21,45",
        "imagem": "img/img-categorias-labios-makemana.jpg",
        "destaque": False,
    },
]


TESTIMONIALS = [
    {
        "nome": "Cliente MakeMana",
        "imagem": "img/img-clientes1-makemana.jpg",
        "texto": "O pedido especial chegou no tempo certo. Foi discreto, simples de acompanhar e me ajudou a manter o controle do meu proprio ritmo.",
    },
    {
        "nome": "Cliente MakeMana",
        "imagem": "img/img-clientes2-makemana.jpg",
        "texto": "Gostei porque pude descrever o que precisava sem pressa. Parece uma compra comum, mas entende quando um detalhe muda tudo.",
    },
    {
        "nome": "Cliente MakeMana",
        "imagem": "img/img-clientes3-makemana.jpg",
        "texto": "Acompanhar o status pelo perfil fez diferenca. Saber que cada etapa estava andando me deixou mais tranquila.",
    },
    {
        "nome": "Cliente MakeMana",
        "imagem": "img/img-clientes4-makemana.jpg",
        "texto": "A navegacao e leve e discreta. Quando precisei mudar de tela rapido, consegui voltar para a rotina sem levantar perguntas.",
    },
]


def product_by_id(product_id: str | None) -> dict | None:
    if not product_id:
        return None
    return next((product for product in PRODUCTS if product["id"] == product_id), None)


def products_by_line(line: str | None = None) -> list[dict]:
    if not line:
        return PRODUCTS
    return [product for product in PRODUCTS if product["linha"] == line or product["categoria"] == line]
