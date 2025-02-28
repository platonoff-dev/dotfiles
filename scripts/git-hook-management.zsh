# Function to copy pre-commit hook from dotfiles to current repo
install_message_hook() {
  # Check if current directory is a git repository
  if [ ! -d ".git" ]; then
    echo "Error: Not a git repository"
    return 1
  fi

  # Check if pre-commit hook exists in dotfiles
  if [ ! -f ~/.dotfiles/git-hooks/prepare-commit-msg ]; then
    echo "Error: Pre-commit hook not found in ~/.dotfiles"
    return 1
  fi

  # Create hooks directory if it doesn't exist
  mkdir -p .git/hooks

  # Copy the pre-commit hook
  cp ~/.dotfiles/git-hooks/prepare-commit-msg .git/hooks/
  
  # Make the hook executable
  chmod +x .git/hooks/prepare-commit-msg
  
  echo "Pre-commit hook successfully copied and made executable"
}

# Function to disable pre-commit hook in current repo
disable_message_hook() {
  # Check if current directory is a git repository
  if [ ! -d ".git" ]; then
    echo "Error: Not a git repository"
    return 1
  fi

  # Check if pre-commit hook exists
  if [ ! -f .git/hooks/prepare-commit-msg ]; then
    echo "Pre-commit hook is not installed"
    return 1
  fi

  # Rename the hook to disable it
  mv .git/hooks/prepare-commit-msg .git/hooks/prepare-commit-msg.disabled
  
  echo "Pre-commit hook disabled"
}

# Function to enable pre-commit hook in current repo
enable_message_hook() {
  # Check if current directory is a git repository
  if [ ! -d ".git" ]; then
    echo "Error: Not a git repository"
    return 1
  fi

  # Check if disabled pre-commit hook exists
  if [ ! -f .git/hooks/prepare-commit-msg.disabled ]; then
    echo "No disabled pre-commit hook found"
    
    # Check if hook exists in dotfiles, offer to install
    if [ -f ~/.dotfiles/git-hooks/prepare-commit-msg ]; then
      echo "Would you like to install the pre-commit hook from your dotfiles? (y/n)"
      read response
      if [[ $response =~ ^[Yy]$ ]]; then
        copy_precommit_hook
      fi
    fi
    return 1
  fi

  # Rename the hook back to enable it
  mv .git/hooks/prepare-commit-msg.disabled .git/hooks/prepare-commit-msg
  
  # Make sure it's executable
  chmod +x .git/hooks/prepare-commit-msg
  
  echo "Pre-commit hook enabled"
}