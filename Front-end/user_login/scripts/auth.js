function handleGoogleLogin(response) {
  fetch('/api/login-google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: response.credential })
  })
  .then(r => r.json())
  .then(usuario => {
    localStorage.setItem('usuario', JSON.stringify(usuario));
    montarMenuPerfil(usuario);
  });
}

function montarMenuPerfil(usuario) {
  const areaLogin = document.querySelector('.butons'); // onde ficam os botões "entrar"/"criar conta"
  
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
  document.getElementById('menuPerfil').classList.toggle('ativo');
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