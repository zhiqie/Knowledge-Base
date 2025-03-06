// app.js

// 城市和子目录选择与文件上传相关功能
const citySelect = document.getElementById('citySelect');
const subDirectorySelect = document.getElementById('subDirectorySelect');
const fileInput = document.getElementById('fileInput');
let selectedCity;

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

window.toggleDirectory = function(element) {
  const container = element.parentElement.querySelector('.directory-children');
  const icon = element.querySelector('i');
  if (container.style.display === 'none' || !container.style.display) {
    container.style.display = 'block';
    icon.classList.replace('fa-folder', 'fa-folder-open');
  } else {
    container.style.display = 'none';
    icon.classList.replace('fa-folder-open', 'fa-folder');
  }
};

async function loadCities() {
  let retries = 0;
  while (retries < MAX_RETRIES) {
    try {
      const response = await fetch('/getCities');
      if (!response.ok) {
        throw new Error('网络请求失败');
      }
      const cities = await response.json();
      citySelect.innerHTML = '<option value="">请选择城市</option>';
      cities.forEach(city => {
        citySelect.innerHTML += `<option value="${city}">${city}</option>`;
      });
      break;
    } catch (error) {
      retries++;
      if (retries < MAX_RETRIES) {
        console.error(`获取城市列表失败，正在进行第 ${retries} 次重试...`, error);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      } else {
        console.error('获取城市列表失败:', error);
        alert('获取城市列表失败，请稍后重试');
      }
    }
  }
}

async function loadSubDirectories() {
  const city = citySelect.value;
  if (!city) return;
  const response = await fetch(`/getSubDirectories?city=${city}&type=business`);
  const data = await response.json();
  subDirectorySelect.style.display = 'block';
  subDirectorySelect.innerHTML = '<option value="">请选择子目录</option>';
  data.structure.forEach(item => {
    if (item.type === 'directory') {
      subDirectorySelect.innerHTML += `<option value="${item.path}">${item.name}</option>`;
    }
  });
}

async function uploadFile() {
  selectedCity = citySelect.value;
  const subDirectory = subDirectorySelect.value;
  if (!selectedCity) return alert('请先选择城市');
  if (!subDirectory) return alert('请先选择子目录');
  const file = fileInput.files[0];
  if (!file) return alert('请选择要上传的文件');
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('city', selectedCity);
    formData.append('subDirectory', subDirectory);
    const response = await fetch('/uploadFile', {
      method: 'POST',
      body: formData
    });
    if (!response.ok) throw new Error('上传失败');
    const data = await response.json();
    alert(data.message || '文件上传成功');
  } catch (error) {
    console.error('上传文件失败:', error);
    alert('文件上传失败');
  }
}

function exportFiles() {
  selectedCity = citySelect.value;
  if (!selectedCity) return alert('请先选择城市');
  window.location.href = `/exportFiles?city=${selectedCity}`;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('mouseenter', () => {
      link.style.transform = 'translateY(-3px) scale(1.05)';
    });
    link.addEventListener('mouseleave', () => {
      link.style.transform = 'none';
    });
  });
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    document.documentElement.style.setProperty('--gradient-pos', `${x * 100}% ${y * 100}%`);
  });
  function renderDirectory(structure, container, level = 0) {
    structure.forEach(item => {
      const div = document.createElement('div');
      div.className = 'directory-item';
      div.style.paddingLeft = `${level * 20}px`;
      if (item.type === 'directory') {
        div.innerHTML = `
          <div class="folder" onclick="toggleDirectory(this)">
            <i class="fas fa-folder${item.children && item.children.length ? '-open' : ''}"></i>
            ${item.name}
            <span class="badge">${item.children ? item.children.length : 0}</span>
          </div>
        `;
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'directory-children';
        childrenContainer.style.display = 'none';
        div.appendChild(childrenContainer);
        renderDirectory(item.children, childrenContainer, level + 1);
      } else {
        div.innerHTML = `
          <div class="file" onclick="downloadFile('${item.path}')">
            <i class="fas fa-file"></i>
            ${item.name}
          </div>
        `;
      }
      container.appendChild(div);
    });
  }
  window.toggleDirectory = function(element) {
    const container = element.parentElement.querySelector('.directory-children');
    const icon = element.querySelector('i');
    if (container.style.display === 'none' || !container.style.display) {
      container.style.display = 'block';
      icon.classList.replace('fa-folder', 'fa-folder-open');
    } else {
      container.style.display = 'none';
      icon.classList.replace('fa-folder-open', 'fa-folder');
    }
  };
  async function loadDirectory(path = '') {
    try {
      selectedCity = citySelect.value;
      if (!selectedCity) {
        alert('请先选择城市');
        return;
      }
      const response = await fetch(`/getSubDirectories?city=${selectedCity}&type=business&path=${encodeURIComponent(path)}`);
      const data = await response.json();
      const container = document.getElementById('directory-container');
      container.innerHTML = '';
      renderDirectory(data.structure, container);
      updateBreadcrumb(path);
    } catch (error) {
      console.error('加载目录失败:', error);
    }
  }
  function updateBreadcrumb(path) {
    const parts = path.split('/').filter(p => p);
    let breadcrumb = '<a href="#" onclick="loadDirectory(\'\')">根目录</a>';
    let accumulatedPath = '';
    parts.forEach((part, index) => {
      accumulatedPath += `${part}/`;
      breadcrumb += ` / <a href="#" onclick="loadDirectory('${accumulatedPath.slice(0, -1)}')">${part}</a>`;
    });
    document.getElementById('breadcrumb').innerHTML = breadcrumb;
  }
  loadCities();
});
