$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms,System.Drawing

$outputPath = Join-Path $PSScriptRoot "screen.png"
$intervalMilliseconds = 100
$failureCount = 0

Write-Host "Refreshing screenshot every $intervalMilliseconds milliseconds."
Write-Host "Saving to: $outputPath"
Write-Host "Press Ctrl+C to stop and delete the screenshot."

try {
    while ($true) {
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

        try {
            $graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bounds.Size)

            $tempPath = "$outputPath.tmp.png"
            $bitmap.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
            Move-Item -LiteralPath $tempPath -Destination $outputPath -Force
            $failureCount = 0
        }
        catch {
            $failureCount++
            if ($failureCount -eq 1 -or $failureCount % 20 -eq 0) {
                Write-Warning "Screenshot capture failed ($failureCount): $($_.Exception.Message)"
            }
        }
        finally {
            $graphics.Dispose()
            $bitmap.Dispose()
        }

        Start-Sleep -Milliseconds $intervalMilliseconds
    }
}
finally {
    Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath "$outputPath.tmp.png" -Force -ErrorAction SilentlyContinue
    Write-Host "Deleted screenshot files."
}
