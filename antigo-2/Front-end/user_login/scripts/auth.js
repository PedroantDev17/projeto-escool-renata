// O login com Google (handleGoogleLogin) fica no JS da página de login/cadastro,
// que salva o usuário e redireciona. Ele não deve ser duplicado aqui.
// Depende de utils.js (escapeHTML, getUsuarioLogado, fotoDoUsuario).

function montarMenuPerfil(usuario) {
    const areaLogin = document.querySelector('.butons'); // onde ficam os botões "entrar"/"criar conta"

    // Páginas sem esse elemento não têm menu para montar
    if (!areaLogin) return;

    areaLogin.innerHTML = `
  <div class="perfil-dropdown" onclick="toggleMenu()">
    <img src="${escapeHTML(fotoDoUsuario(usuario))}" class="avatar" alt="Foto de perfil" />
    <div class="dropdown-content" id="menuPerfil">
      <span class="nome-usuario">${escapeHTML(usuario.nome)}</span>
      <a href="#" onclick="abrirPerfil(event)">Meu perfil</a>
      <a href="#" onclick="abrirFavoritos(event)">Favoritos</a>
      <a href="#" onclick="abrirConfiguracoes(event)">Configurações</a>
      <a href="#" onclick="sair(event)">Sair</a>
    </div>
  </div>
`;
}

function toggleMenu() {
    const menu = document.getElementById('menuPerfil');
    if (menu) menu.classList.toggle('ativo');
}

function sair(event) {
    if (event) event.preventDefault();
    localStorage.removeItem('usuario');
    location.reload();
}

// Fecha o menu ao clicar fora dele
document.addEventListener('click', function (event) {
    const dropdown = document.querySelector('.perfil-dropdown');
    const menu = document.getElementById('menuPerfil');
    if (dropdown && menu && !dropdown.contains(event.target)) {
        menu.classList.remove('ativo');
    }
});

// addEventListener (em vez de window.onload) para não sobrescrever outros scripts
window.addEventListener('load', function () {
    const usuario = getUsuarioLogado();
    if (usuario) {
        montarMenuPerfil(usuario);
    }
});
