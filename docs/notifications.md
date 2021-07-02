# Serviço de notificação

## Caso de uso (história do usuário)
Como um usuário, eu gostaria de receber notificações quando meu nome aparecer em alguma das listas de vacinação.
Idealmente, após eu fazer uma busca, me é dada a opção para receber notificações em caso de novos aparecimentos.

Essas notificações podem ser email e/ou whatsapp.

Apenas um envio por aparecimento em nova lista. No caso de eu me esquecer que já me cadastrei com meu email para um determinado nome e me cadastrar novamente com esse mesmo par nome-email, não quero receber 2x.
Quando eu receber uma mensagem, gostaria de ter a opção de me desinscrever de novos envios.

## Notas técnicas
- Continuando a abordagem de baixo custo, não usaremos um serviço de banco de dados para essa funcionalidade. Em vez disso, continuaremos usando S3 para persistência.
- Dois novos índices serão escritos:
    - subscriptions.json
    - unsubscribed.json

### subscriptions.json
**Opção 1**
Esse objeto contém como chave o nome que foi buscado,
e como valor uma lista de inscrições para receber notificações.
```json
{
    "ana maria de souza": [
        // Cada entrada da lista representa uma inscrição para esse nome
        {
            "phone": "085991231234",
            "email": "ana.maria.178237832@gmail.com",
            "subscribed_at": 13214654132,
        },
        {
            "phone": "085993214321",
            "email": "maria.ana.54356457@gmail.com",
            "subscribed_at": 13214654132,
        },
    ]
}
```

**Opção 2**
Essa lista contém cada inscrição que foi feita,
sendo as chaves os nomes e os valores as inscrições.
```json
[
    // Cada entrada representa uma inscrição por completo
    {
        "ana maria de souza": {
            "phone": "085991231234",
            "email": "ana.maria.178237832@gmail.com",
            "subscribed_at": 13214654132,
        },
    },
    {
        "ana maria de souza": {
            "phone": "085993214321",
            "email": "maria.ana.54356457@gmail.com",
            "subscribed_at": 13214654132,
        },
    }
]
```

### unsubscribed.json
TBD...
