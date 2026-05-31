# 轮回之战 — Roguelike 生存

## 版本管理规则

### 🏷️ 版本标签
每次更新代码后，按顺序打标签：`v1`, `v2`, `v3` ...

```bash
git tag v<N> -f
git push origin v<N>
```

### 📦 版本保留策略
- 最多保留 **10 个版本标签**（`v1` ~ `v10`）
- 超过 10 个时，删除最早的版本
- 删除旧版本命令：
```bash
# 列出所有版本标签，按数字排序
$tags = git tag --sort=version:refname
# 如果超过10个，删除最旧的
if ($tags.Count -gt 10) {
    $oldest = $tags[0]
    git tag -d $oldest
    git push origin --delete $oldest
}
```

### 🔄 更新流程
1. 修改代码并测试
2. `git add -A && git commit -m "v<N> 更新说明"`
3. `git push origin main`
4. 打标签并推送

### 🔑 代理
推送时需要通过 SakuraCat 代理: `http://127.0.0.1:7897`

### 📎 远程仓库
`https://github.com/aww258369/roguelike-game`
