# === Настрой исключаемые каталоги ===
$excludeDirs = @(
    '.git',
    '.gitlab-ci.yml',
    '.gitignore',
    '.idea',
    'logs',
    'data',
    '.venv',
    'venv',
    '_CI_CD',
    '__pycache__',
    '.pytest_cache',
    'tests',
    'prepare_folder_ci_cd.ps1',
    'poetry.lock'
)

# Получить имя текущей директории
$currentDir = Split-Path -Leaf (Get-Location)
$targetDir = "$currentDir"+"_CI_CD"

# Динамически добавить целевую папку к исключениям (если она вдруг отличается по имени)
if ($excludeDirs -notcontains $targetDir) {
    $excludeDirs += $targetDir
}

# === Укажи исключаемые файлы (по точному имени) ===
$excludeFiles = @(
    '.gitignore',
    '.env',
    '.*_CI_CD'
)

# === Укажи маски файлов для исключения (wildcards) ===
$excludeFilePatterns = @(
    '*.pyc',
    '*.yaml',
    '*.yml',
    '*.log',
    '*.tmp',
    '*.ps1'
)

# Создать целевой каталог, если его нет
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
}

function Copy-With-Exclude {
    param (
        [string]$source,
        [string]$dest,
        [string[]]$excludeDirs,
        [string[]]$excludeFiles,
        [string[]]$excludeFilePatterns
    )
    Get-ChildItem -Path $source -Force | ForEach-Object {
        # Исключение директорий по имени
        if ($_.PSIsContainer -and ($excludeDirs -contains $_.Name)) {
            return
        }
        # Исключение файлов по точному имени
        if (-not $_.PSIsContainer -and ($excludeFiles -contains $_.Name)) {
            return
        }
        # Исключение файлов по маске
        if (-not $_.PSIsContainer) {
            foreach ($pattern in $excludeFilePatterns) {
                if ($_.Name -like $pattern) { return }
            }
        }
        $targetPath = Join-Path $dest $_.Name
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
            Copy-With-Exclude -source $_.FullName -dest $targetPath -excludeDirs $excludeDirs -excludeFiles $excludeFiles -excludeFilePatterns $excludeFilePatterns
        } else {
            Copy-Item -Path $_.FullName -Destination $targetPath -Force
        }
    }
}

Copy-With-Exclude -source "." -dest $targetDir -excludeDirs $excludeDirs -excludeFiles $excludeFiles -excludeFilePatterns $excludeFilePatterns
