document.addEventListener("DOMContentLoaded", function() {
    loadCities(); // 页面加载时获取城市列表
});

// 获取城市列表，调用新接口 /api/city/getCities
function loadCities() {
    fetch("/api/city/getCities")
        .then(response => {
            if (!response.ok) {
                throw new Error("加载城市列表失败，HTTP状态码：" + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("加载到的城市数据：", data);
            let citySelect = document.getElementById("citySelect");
            if (!citySelect) {
                console.error("找不到用于显示城市的元素，请确认 index.html 中有 id 为 'citySelect' 的元素。");
                return;
            }
            // 清空原有选项并添加新选项
            citySelect.innerHTML = "";
            if (data.length === 0) {
                citySelect.innerHTML = "<option value=''>无数据</option>";
            } else {
                data.forEach(city => {
                    let option = document.createElement("option");
                    option.value = city;
                    option.text = city;
                    citySelect.appendChild(option);
                });
                // 默认加载第一个城市的目录
                loadDirectories(data[0]);
            }
        })
        .catch(error => {
            console.error("获取城市列表时出错:", error);
            alert("获取城市列表失败，请稍后重试");
        });
}

// 加载指定城市下的子目录，调用接口 /api/city/{city}/directories
function loadDirectories(city) {
    fetch(`/api/city/${encodeURIComponent(city)}/directories`)
        .then(response => {
            if (!response.ok) {
                throw new Error("加载目录失败，HTTP状态码：" + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("加载到的目录数据：", data);
            let dirSelect = document.getElementById("directorySelect");
            if (!dirSelect) {
                console.error("找不到用于显示目录的元素，请确认页面中有 id 为 'directorySelect' 的元素。");
                return;
            }
            // data 结构假设为 { directories: ["合同库", "视频库", "文档库"] }
            dirSelect.innerHTML = "";
            if (data.directories && data.directories.length > 0) {
                data.directories.forEach(dir => {
                    let option = document.createElement("option");
                    option.value = dir;
                    option.text = dir;
                    dirSelect.appendChild(option);
                });
            } else {
                dirSelect.innerHTML = "<option value=''>无目录</option>";
            }
        })
        .catch(error => {
            console.error("获取目录时出错:", error);
            alert("获取目录失败，请稍后重试");
        });
}

// 当城市下拉框值改变时，加载对应的目录
document.getElementById("citySelect")?.addEventListener("change", function(event) {
    let selectedCity = event.target.value;
    if (selectedCity) {
        loadDirectories(selectedCity);
    }
});
