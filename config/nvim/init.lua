-- Basic settings
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.mouse = 'a'
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.hlsearch = true
vim.opt.incsearch = true
vim.opt.wrap = false
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true
vim.opt.smartindent = true
vim.opt.termguicolors = true
vim.opt.signcolumn = 'yes'
vim.opt.updatetime = 250
vim.opt.clipboard = 'unnamedplus'
vim.opt.undofile = true
vim.opt.scrolloff = 8

-- Leader key
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Key mappings
local keymap = vim.keymap.set
local opts = { noremap = true, silent = true }

-- Better window navigation
keymap('n', '<C-h>', '<C-w>h', opts)
keymap('n', '<C-j>', '<C-w>j', opts)
keymap('n', '<C-k>', '<C-w>k', opts)
keymap('n', '<C-l>', '<C-w>l', opts)

-- Clear search highlight
keymap('n', '<Esc>', ':nohlsearch<CR>', opts)

-- Better indenting
keymap('v', '<', '<gv', opts)
keymap('v', '>', '>gv', opts)

-- Move lines
keymap('v', 'J', ":m '>+1<CR>gv=gv", opts)
keymap('v', 'K', ":m '<-2<CR>gv=gv", opts)

-- Save with Ctrl+S
keymap('n', '<C-s>', ':w<CR>', opts)
keymap('i', '<C-s>', '<Esc>:w<CR>', opts)
