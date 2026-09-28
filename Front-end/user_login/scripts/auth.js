// O login com Google (handleGoogleLogin) fica no JS da página de login,
// que salva o usuário e redireciona. Ele não deve ser duplicado aqui.

function montarMenuPerfil(usuario) {
  const areaLogin = document.querySelector('.butons'); // onde ficam os botões "entrar"/"criar conta"

  // Páginas sem esse elemento (como a de login) não têm menu para montar
  if (!areaLogin) return;

  areaLogin.innerHTML = `
  <div class="perfil-dropdown" onclick="toggleMenu()">
    <img src="${usuario.foto}" class="avatar" alt="Foto de perfil" />
    <div class="dropdown-content" id="menuPerfil">
      <span class="nome-usuario">${usuario.nome}</span>
      <a  onclick="abrirPerfil(event)">Meu perfil</a>
      <a  onclick="abrirFavoritos(event)">Favoritos</a>
      <a  onclick="abrirConfiguracoes(event)">Configurações</a>
      <a  onclick="sair()">Sair</a>
    </div>
  </div>
`;
}

function toggleMenu() {
  const menu = document.getElementById('menuPerfil');
  if (menu) menu.classList.toggle('ativo');
}


function sair() {
  localStorage.removeItem('usuario');
  location.reload();
}

document.addEventListener('click', function(event) {
  const dropdown = document.querySelector('.perfil-dropdown');
  const menu = document.getElementById('menuPerfil');
  if (dropdown && menu && !dropdown.contains(event.target)) {
    menu.classList.remove('ativo');
  }
});


window.onload = function() {
  const usuarioSalvo = localStorage.getItem('usuario');
  if (usuarioSalvo) {
    montarMenuPerfil(JSON.parse(usuarioSalvo));
  }
};