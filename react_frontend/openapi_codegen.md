// 用于根据 openapi.json 自动生成 TypeScript 类型和 API 方法
// 推荐使用 openapi-typescript-codegen 或类似工具

// 1. 安装依赖
// npm install openapi-typescript-codegen --save-dev

// 2. 生成 types/api.ts
// npx openapi-typescript-codegen --input ../openapi.json --output ./src/services/api_gen --client axios

// 3. 替换前端 axios 直接调用为类型安全的 API 方法

// 4. 可选：在 package.json scripts 添加自动生成命令
// "generate:api": "npx openapi-typescript-codegen --input ../openapi.json --output ./src/services/api_gen --client axios"

// 5. 参考文档：https://github.com/ferdikoomen/openapi-typescript-codegen
