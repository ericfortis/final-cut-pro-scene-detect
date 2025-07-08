on run
  do shell script "/opt/homebrew/bin/fcpscene --gui"
end run

on open droppedItems
  set cmd to "/opt/homebrew/bin/fcpscene --gui"

  if (count of droppedItems) > 0 then
    set quotedInput to quoted form of POSIX path of item 1 of droppedItems
    set cmd to cmd & " " & quotedInput
  end if

  do shell script cmd
end open
