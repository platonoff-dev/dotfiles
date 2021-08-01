# Path to your oh-my-zsh installation.
export ZSH="/home/anatoliy/.oh-my-zsh"

ZSH_THEME="robbyrussell"

plugins=(git)

source $ZSH/oh-my-zsh.sh

eval "$(starship init zsh)"

alias ls=exa
alias cat=bat
alias gc="git commit"
alias ga="git add"
alias gpl="git pull"
alias gph="git push"


[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

export PATH="$HOME/.poetry/bin:$PATH"

export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

export PATH="$HOME/.lein:$PATH"

export PATH="/home/anatoliy/.local/bin:$PATH"

export PATH=$PATH:/usr/local/go/bin
