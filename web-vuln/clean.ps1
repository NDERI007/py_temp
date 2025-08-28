Write-Host "Cleaning python build and cache files.."

$patterns = @("__pycache__",".pytest_cache")

foreach($pattern in $patterns){
    $items = Get-ChildItem -Path . -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -like $pattern}

    foreach($item in $items){
        try{
            Remove-item -Recurse -Force $item.FullName -ErrorAction Stop
            Write-Host "Removed $($item.FullName)"
        }
        catch{
            if($_.CategoryInfo.Reason -eq "ItemNotFoundException"){
            #Ignore missing items
            continue
           }
            else{
                Write-Warning "Could not remove $($item.FullName): $($_.Exception.Message)"
            }
        }
    }
}

Write-Host "Cleanup complete ✅"
   