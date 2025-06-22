" Bannarizer.vim - A script to create text banners, compatible with IdeaVim.
"
" Installation:
" 1. This script requires Tim Pope's vim-repeat plugin for '.' functionality.
"    In IntelliJ/IdeaVim, go to File > Settings > Plugins, search for and install
"    "IdeaVim-EasyMotion" which bundles vim-repeat.
"
" 2. Save this file somewhere, e.g., ~/.config/ideavim/bannarizer.vim
"
" 3. Add the following line to your ~/.ideavimrc file:
"    source ~/.config/ideavim/bannarizer.vim
echom "Bannarizer loaded"
echom "Starting bannarizer.vim..."
call append(line('$'), "bannarizer.vim loaded")  " appends a visible line at the end of the current buffer
" --- Guard against re-sourcing ---
if exists("g:loaded_bannarizer")
  finish
endif
let g:loaded_bannarizer = 1

" --- Configuration ---
let s:default_width = 96

"=============================================================================
"  Core Functions
"=============================================================================

" Creates a single banner line from text.
" Returns the new line, or an empty string on error.
function! s:CreateBannerFromText(line_content, width)
  let l:total_width = a:width

  " Get the comment prefix from 'commentstring', fallback to '#'
  let l:cs = &commentstring
  if empty(l:cs)
    let l:cs = '# %s'
  endif
  " Extract the part before '%s'
  let l:comment_prefix = trim(matchstr(l:cs, '.*\ze%s'))

  " Clean the text
  let l:text = a:line_content
  let l:text = substitute(l:text, '^\s*' . escape(l:comment_prefix, '.*[]\') . '\+\s*', '', '')
  let l:text = substitute(l:text, '=', '', 'g')
  let l:text = toupper(trim(l:text))

  if empty(l:text)
    return a:line_content
  endif

  let l:spaced_text = ' ' . l:text . ' '
  let l:min_width = len(l:comment_prefix) + 1 + len(l:spaced_text) + 2
  if l:total_width < l:min_width
    echohl ErrorMsg
    echo "Bannarizer Error: Text too long for width " . l:total_width . " (needs " . l:min_width . ")"
    echohl None
    return '' " Signal error with an empty string
  endif

  let l:remaining = l:total_width - len(l:comment_prefix) - 1 - len(l:spaced_text)
  let l:left = floor(l:remaining / 2)
  let l:right = l:remaining - l:left

  return printf('%s %s%s%s', l:comment_prefix, repeat('=', l:left), l:spaced_text, repeat('=', l:right))
endfunction

" Bannarizes a range of lines. This is the main workhorse function.
function! s:Bannarize(firstline, lastline, ...)
  " Determine width: argument -> last used -> 'textwidth' -> default
  let l:width_arg = get(a:, 1, '')
  if !empty(l:width_arg)
    let l:width = l:width_arg
  elseif exists("b:bannarizer_last_width")
    let l:width = b:bannarizer_last_width
  elseif &textwidth > 0
    let l:width = &textwidth
  else
    let l:width = s:default_width
  endif

  " Store the width for the next repeat/use in this buffer
  let b:bannarizer_last_width = l:width

  " Process each line in the range
  for lnum in range(a:firstline, a:lastline)
    let l:original_line = getline(lnum)
    let l:new_line = s:CreateBannerFromText(l:original_line, l:width)
    " Only update the line if banner creation didn't fail
    if !empty(l:new_line)
      call setline(lnum, l:new_line)
    endif
  endfor

  " Set up the repeat mapping
  if exists("*repeat#set")
    call repeat#set(":BannarizerRepeat\r")
  endif
endfunction

" Repeats the last bannarize action on the current line.
function! s:RepeatLast()
  " Call the main function on the current line, using the last stored width
  call s:Bannarize(line('.'), line('.'), get(b:, 'bannarizer_last_width', ''))
  " Re-set the repeat mapping so we can press '.' again
  if exists("*repeat#set")
    call repeat#set(":BannarizerRepeat\r")
  endif
endfunction

" Prompts the user for a width and then bannarizes the selection or current line.
function! s:PromptAndBannarize()
  " Determine the line range (visual mode or current line)
  let [l:l1, l:l2] = [line("."), line(".")]
  if mode() =~# '^[vV]'
    let [l:l1, l:l2] = [line("'<"), line("'>")]
    if mode() =~# '^[vV]'
    " Exit visual mode
      execute "normal! gv\<Esc>"
    endif
  endif

  " Determine a default width to show in the prompt
  let l:default_width = get(b:, 'bannarizer_last_width', &textwidth > 0 ? &textwidth : s:default_width)

  let l:width_input = input('Enter banner width: ', l:default_width)

  " Abort if user cancelled or entered nothing
  if empty(l:width_input)
    return
  endif

  " Validate input is a number
  if l:width_input !~# '^\d\+$'
    echohl ErrorMsg | echo "Invalid width: " . l:width_input | echohl None
    return
  endif

  " Call the main function with the specified range and new width
  call s:Bannarize(l:l1, l:l2, l:width_input)
endfunction


"=============================================================================
"  Commands and Mappings
"=============================================================================

command! -range -nargs=? Bannarize call s:Bannarize(<line1>, <line2>, <q-args>)
command! BannarizerRepeat call s:RepeatLast()
command! BannarizePrompt call s:PromptAndBannarize()

echo "Bannarizer loaded."

" You can customize the leader key here
" let mapleader = "\<Space>"

nnoremap <silent> <Leader>m :Bannarize<CR>
vnoremap <silent> <Leader>m :Bannarize<CR>

nnoremap <silent> <Leader>T :BannarizePrompt<CR>
vnoremap <silent> <Leader>T :BannarizePrompt<CR>
