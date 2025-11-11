## 使用示例

### 1. 返回随机图片数据

```
GET /api/images?format=image
```

**响应**：直接返回图片二进制数据，Content-Type 为 `image/jpeg` 等

### 2. 返回最新图片数据

```
GET /api/images/latest?format=image
```

**响应**：直接返回最新图片的二进制数据

### 3. 返回指定位置图片数据

```
GET /api/images/position/5?format=image
```

**响应**：直接返回第 6 张图片的二进制数据

### 4. JSON 格式（保持不变）

```
GET /api/images
GET /api/images/latest
GET /api/images/position/0
```
