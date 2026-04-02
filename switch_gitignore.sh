#!/bin/bash

# 切换 .gitignore 文件的脚本

if [ "$1" == "local" ]; then
  git config core.excludesfile .gitignore.local
  echo "已切换到本地 .gitignore.local"
elif [ "$1" == "github" ]; then
  git config core.excludesfile .gitignore.github
  echo "已切换到 GitHub .gitignore.github"
else
  echo "用法: $0 {local|github}"
  echo "  local: 使用本地 .gitignore.local"
  echo "  github: 使用 GitHub .gitignore.github"
  exit 1
fi

echo "当前使用的 .gitignore 文件: $(git config core.excludesfile)"
