# glycine
echo
echo \ \ \ \ \ ┌───────────────────────────────────────────────────────────┐
echo \ \ \ \ \ │\ \ \ \ \ \ \ \ \ \ \ \ \ 欢迎来到石家庄东华金龙化工有限公司\ \ \ \ \ \ \ \ \ \ \ \ │
echo \ \ \ \ \ │\ Welcome To Shijiazhuang DONGHUA JINLONG Chemical Co., LTD\ │
echo \ \ \ \ \ └───────────────────────────────────────────────────────────┘
echo

# Completion settings

# history substring searching
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search

zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search

bindkey '^[[A' up-line-or-beginning-search
bindkey '^[[B' down-line-or-beginning-search

autoload -Uz compinit
# Case-insensitive tab completion
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

compinit

# Enable prompt subsystem
autoload -Uz promptinit
promptinit

# Colours
autoload -U colors && colors

# History settings
HISTFILE=~/.cache/zsh/history
HISTSIZE=1000000 # 1 million
SAVEHIST=1000000
setopt HIST_IGNORE_ALL_DUPS HIST_REDUCE_BLANKS

# oh-my-zsh git library - needed for theme
source ~/.config/zsh/plugins/omz-lib/git.zsh

# Theme
source ~/.config/zsh/themes/passion/passion.zsh-theme

# Plugins
source ~/.config/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.config/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# Path stuff
export PATH=$HOME/.local/bin:$PATH

# Ruby Gems
export PATH=$HOME/.local/share/gem/ruby/3.0.0/bin:$PATH
export PATH=$HOME/gems/bin:$PATH
export GEM_HOME="$HOME/gems"

# Epic Games
export PATH=$HOME/.local/bin/wine-ge/lutris-GE-Proton8-25-x86_64/bin/:$PATH

# peaclock
alias peaclock="peaclock --config-dir ~/.config/peaclock"

# Clean chroot to build AUR packages
export CHROOT=$HOME/AUR/CHROOT

# Aliases for coloured output
alias ls='ls --color=auto'
alias grep='grep --color=auto'
export LESS='-R --use-color -Dd+r$Du+b$'
alias ip='ip -color=auto'
export MANPAGER="less -R --use-color -Dd+r -Du+b"

# Required for GPG to prompt for passphrase in terminal
export GNUPGHOME="$HOME/.local/share/gnupg"
export GPG_TTY=$(tty)
gpgconf --launch gpg-agent
