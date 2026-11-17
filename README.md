# Peritão

Sistema interno do 1º Núcleo Regional de Perícia Criminal – Araguatins (Polícia Científica do Tocantins).

Registro e consulta de ocorrências periciais. Aplicativo web instalável pelo celular,
sem loja de aplicativos, com gravação offline e envio automático quando a conexão volta.

## Telas

- **Nova** — formulário de registro em campo
- **Minhas** — ocorrências do perito no ano, com contagem de laudo pendente
- **Buscar** — por protocolo, BO, vítima ou local
- **Conta** — fila de envio e sessão

## Dados

Os dados ficam no Supabase, protegidos por Row Level Security. Nada é armazenado
neste repositório além do código do app e da chave publicável, que é feita para
ficar no navegador.

## Arquivos

| Arquivo | Função |
|---|---|
| `index.html` | O app inteiro: interface, lógica e estilos |
| `manifest.json` | Instalação na tela de início |
| `sw.js` | Service worker — abre sem rede |
| `icon-*.png` | Ícones |
