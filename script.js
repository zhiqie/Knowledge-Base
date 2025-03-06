// script.js

// 获取城市参数
const urlParams = new URLSearchParams(window.location.search);
const city = urlParams.get('city');

// 设置城市名称
document.querySelector('h3').textContent = city;

// 获取所有展开按钮和对应的子列表
const expandButtons = document.querySelectorAll('.expand');
const subLists = document.querySelectorAll('.sub-list');

// 隐藏所有子列表
function hideAllSubLists() {
    subLists.forEach(subList => {
        subList.style.display = 'none';
    });
}

// 添加展开按钮的点击事件处理程序
expandButtons.forEach(button => {
    button.addEventListener('click', function () {
        // 找到按钮所在的父元素
        const parentLi = button.parentElement;

        // 找到按钮下的子列表
        const subList = parentLi.querySelector('.sub-list');

        // 如果子列表存在，则切换其显示状态
        if (subList) {
            if (subList.style.display === 'none' || subList.style.display === '') {
                subList.style.display = 'block';
            } else {
                subList.style.display = 'none';
            }
        }
    });
});

// 获取所有需要合并查询的输入元素和下拉框
const searchInput = document.getElementById('searchInput');
const filterOption = document.getElementById('filterOption');

// 当表单提交时，获取输入框和下拉框的值，并执行合并查询
document.getElementById('searchForm').addEventListener('submit', function(e) {
    e.preventDefault(); // 阻止表单默认提交行为

    const query = searchInput.value.trim(); // 获取输入框的值
    const filter = filterOption.value; // 获取下拉框的值

    // 检查下拉框的值是否为"全部"
    if (filter === '全部') {
        console.log(`Query: ${query}, Filter: ${filter}`);
    } else if (query && filter) {
        // 执行合并查询逻辑（根据输入框的内容和下拉框选项的值）
        console.log(`Query: ${query}, Filter: ${filter}`);
        // 在这里可以编写合并查询代码，比如发送请求到服务器进行查询等
    } else {
        // 如果查询关键字或筛选选项为空，给出提示信息
        alert('请输入查询关键字并选择筛选选项！');
    }
});

const initKnowledgeBase = (() => {
    const manager = new KnowledgeManager();
    
    // 绑定文件操作
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
    document.getElementById('exportBtn').onclick = exportData;
  
    // 增强搜索功能
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', debounce(searchHandler, 300));
})();
  
// 示例：修改原有表单提交
document.getElementById('searchForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const results = new KnowledgeManager().search({
      keyword: this.searchInput.value,
      category: this.filterOption.value
    });
    renderResults(results);
});
