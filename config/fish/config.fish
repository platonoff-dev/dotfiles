# Fish shell configuration

# Disable greeting
set -g fish_greeting

# Environment
set -gx EDITOR nvim
set -gx VISUAL nvim

# Path additions for language tools
fish_add_path ~/.cargo/bin
fish_add_path ~/go/bin
fish_add_path ~/.local/bin

# Aliases
alias ls='eza'
alias ll='eza -la'
alias la='eza -a'
alias lt='eza --tree'
alias cat='bat'
alias vim='nvim'
alias v='nvim'
alias g='git'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gs='git status'
alias gd='git diff'
alias ..='cd ..'
alias ...='cd ../..'

# FZF integration
if command -v fzf &>/dev/null
    fzf --fish | source
end

# Starship prompt
if command -v starship &>/dev/null
    starship init fish | source
end

# Local config
if test -f ~/.config/fish/config.local.fish
    source ~/.config/fish/config.local.fish
end
