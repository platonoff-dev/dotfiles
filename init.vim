lua require('plugins')
lua require('terminal')

colorscheme sublimemonokai

augroup packer_user_config
  autocmd!
  autocmd BufWritePost plugins.lua source <afile> | PackerCompile
augroup end

let g:airline_powerline_fonts = 1
let g:airline#extensions#keymap#enabled = 0
let g:airline_section_z = "\ue0a1:%l/%L Col:%c" "
let g:Powerline_symbols='unicode'
let g:airline#extensions#xkblayout#enabled = 0

source $HOME/.config/nvim/general/settings.vim

