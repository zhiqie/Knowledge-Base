// 初始化 Quill 富文本编辑器
let quill;

document.addEventListener('DOMContentLoaded', () => {
    quill = new Quill('#editContent', {
        theme: 'snow',
        modules: {
            toolbar: [
                [{ 'header': [1, 2, false] }],
                ['bold', 'italic', 'underline'],
                ['image', 'code-block']
            ]
        }
    });

    loadQuestions();
});

// 打开编辑模态框
async function startEdit(id) {
    try {
        const res = await fetch(`/faq/${id}`);
        if (!res.ok) throw new Error('加载失败');
        
        const data = await res.json();
        document.getElementById('editId').value = data.id;
        document.getElementById('editTitle').value = data.title;
        document.getElementById('editType').value = data.type;
        quill.root.innerHTML = data.content;
        
        document.getElementById('modalTitle').textContent = '编辑问题';
        showModal();
    } catch (error) {
        console.error('编辑失败:', error);
    }
}

// 删除问题
async function deleteQuestion(id) {
    if (!confirm('确定删除该问题吗？')) return;
    
    try {
        const res = await fetch(`/faq/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('删除失败');
        loadQuestions();
    } catch (error) {
        console.error('删除失败:', error);
    }
}

// 查看问题
async function viewQuestion(id) {
    try {
        const res = await fetch(`/faq/${id}`);
        if (!res.ok) throw new Error('加载失败');
        
        const data = await res.json();
        document.getElementById('viewTitle').textContent = data.title;
        document.getElementById('viewContent').innerHTML = `
            <p><strong>类型:</strong> ${data.tags.join(', ')}</p>
            <p><strong>内容:</strong></p>
            <div>${data.content}</div>
        `;
        showViewModal();
    } catch (error) {
        console.error('查看失败:', error);
    }
}

// 模态框控制
function showCreateModal() {
    document.getElementById('faqForm').reset();
    document.getElementById('editId').value = '';
    document.getElementById('modalTitle').textContent = '新建问题';
    quill.root.innerHTML = '';
    showModal();
}

function showModal() {
    document.getElementById('formModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('formModal').style.display = 'none';
}

function showViewModal() {
    document.getElementById('viewModal').style.display = 'block';
}

function closeViewModal() {
    document.getElementById('viewModal').style.display = 'none';
}

// 全局点击关闭
window.onclick = function(event) {
    const formModal = document.getElementById('formModal');
    const viewModal = document.getElementById('viewModal');
    if (event.target === formModal) {
        closeModal();
    } else if (event.target === viewModal) {
        closeViewModal();
    }
};

// 加载问题列表
async function loadQuestions() {
    try {
        const search = document.getElementById('searchInput').value.trim();
        const typeFilter = document.getElementById('typeFilter').value;
        const res = await fetch(`/faq?search=${encodeURIComponent(search)}&tag=${encodeURIComponent(typeFilter)}`);
        if (!res.ok) throw new Error('加载失败');
        
        const data = await res.json();
        const tbody = document.getElementById('faqTableBody');
        tbody.innerHTML = data.map(q => `
            <li class="faq-item">
                <div class="faq-info">
                    <div class="faq-title">${q.title}</div>
                    <div class="faq-meta">
                        <span>${new Date(q.created_at).toLocaleString()}</span>
                        <span>${q.tags.join(', ')}</span>
                    </div>
                </div>
                <div class="faq-actions">
                    <button class="btn btn-primary" onclick="viewQuestion(${q.id})">查看</button>
                    <button class="btn btn-primary" onclick="startEdit(${q.id})">编辑</button>
                    <button class="btn btn-danger" onclick="deleteQuestion(${q.id})">删除</button>
                </div>
            </li>
        `).join('');
    } catch (error) {
        console.error('加载问题列表失败:', error);
    }
}

// 提交表单
document.getElementById('faqForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const id = document.getElementById('editId').value;
    const title = document.getElementById('editTitle').value;
    const type = document.getElementById('editType').value;
    const content = quill.root.innerHTML;
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/faq/${id}` : '/faq';
    
    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, tags: [type] })
        });
        if (!res.ok) throw new Error('保存失败');
        closeModal();
        loadQuestions();
    } catch (error) {
        console.error('保存失败:', error);
    }
});