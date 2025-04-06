use std::env;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitStatus};
use std::fs;
use std::io;

/// 平台类型
#[derive(Debug, Clone, Copy)]
enum Platform {
    Windows,
    Linux,
    MacOS,
    All,
}

impl Platform {
    fn from_string(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "windows" | "win" => Some(Platform::Windows),
            "linux" | "ubuntu" | "debian" => Some(Platform::Linux),
            "macos" | "mac" | "darwin" => Some(Platform::MacOS),
            "all" => Some(Platform::All),
            _ => None,
        }
    }
    
    fn target_name(&self) -> &'static str {
        match self {
            Platform::Windows => "windows",
            Platform::Linux => "linux",
            Platform::MacOS => "mac",
            Platform::All => "all",
        }
    }
}

/// 编译结果
struct BuildResult {
    platform: Platform,
    status: ExitStatus,
    output_dir: PathBuf,
}

/// 编译客户端
fn build_client(platform: Platform, client_dir: &Path) -> io::Result<BuildResult> {
    println!("🚀 开始编译 {} 版本...", platform.target_name());
    
    // 运行npm命令
    let npm_install_status = Command::new("npm")
        .arg("install")
        .current_dir(client_dir)
        .status()?;
        
    if !npm_install_status.success() {
        eprintln!("❌ npm install 失败");
        return Ok(BuildResult {
            platform,
            status: npm_install_status,
            output_dir: client_dir.to_path_buf(),
        });
    }
    
    // 确定构建命令参数
    let build_args = match platform {
        Platform::Windows => vec!["run", "build", "--", "--win"],
        Platform::Linux => vec!["run", "build", "--", "--linux"],
        Platform::MacOS => vec!["run", "build", "--", "--mac"],
        Platform::All => vec!["run", "build"]
    };
    
    // 运行构建命令
    let build_status = Command::new("npm")
        .args(&build_args)
        .current_dir(client_dir)
        .status()?;
    
    let output_dir = client_dir.join("dist");
    
    Ok(BuildResult {
        platform,
        status: build_status,
        output_dir,
    })
}

/// 获取电子客户端目录
fn get_client_dir() -> PathBuf {
    let current_dir = env::current_dir().expect("无法获取当前目录");
    
    // 先检查当前目录下是否有kimi-electron-client
    let client_dir = current_dir.join("kimi-electron-client");
    if client_dir.exists() && client_dir.is_dir() {
        return client_dir;
    }
    
    // 如果不在当前目录，则检查父目录
    let parent_dir = current_dir.parent().expect("无法获取父目录");
    let client_dir = parent_dir.join("kimi-electron-client");
    if client_dir.exists() && client_dir.is_dir() {
        return client_dir;
    }
    
    // 最后尝试项目根目录
    let project_root = Path::new(env!("CARGO_MANIFEST_DIR"));
    project_root.join("kimi-electron-client")
}

/// 创建输出目录
fn create_output_dir(output_base_dir: &Path) -> io::Result<PathBuf> {
    let output_dir = output_base_dir.join("releases");
    fs::create_dir_all(&output_dir)?;
    Ok(output_dir)
}

/// 拷贝构建产物到输出目录
fn copy_build_artifacts(build_result: &BuildResult, output_dir: &Path) -> io::Result<()> {
    if !build_result.status.success() {
        println!("⚠️ {} 版本构建失败，跳过文件复制", build_result.platform.target_name());
        return Ok(());
    }
    
    println!("📦 正在复制 {} 版本构建产物...", build_result.platform.target_name());
    
    let platform_output_dir = output_dir.join(build_result.platform.target_name());
    fs::create_dir_all(&platform_output_dir)?;
    
    // 源目录
    let source_dir = match build_result.platform {
        Platform::Windows => build_result.output_dir.join("win-unpacked"),
        Platform::Linux => build_result.output_dir.join("linux-unpacked"),
        Platform::MacOS => build_result.output_dir.join("mac"),
        Platform::All => build_result.output_dir.clone(),
    };
    
    // 复制所有文件
    copy_dir_all(&source_dir, &platform_output_dir)?;
    
    // 复制安装包
    let installer_patterns = match build_result.platform {
        Platform::Windows => vec!["*.exe"],
        Platform::Linux => vec!["*.AppImage", "*.deb"],
        Platform::MacOS => vec!["*.dmg"],
        Platform::All => vec!["*.exe", "*.AppImage", "*.deb", "*.dmg"],
    };
    
    for pattern in installer_patterns {
        for entry in glob::glob(&build_result.output_dir.join(pattern).to_string_lossy())? {
            if let Ok(path) = entry {
                let file_name = path.file_name().unwrap();
                let dest_path = platform_output_dir.join(file_name);
                fs::copy(&path, &dest_path)?;
                println!("✅ 已复制安装包: {:?}", dest_path);
            }
        }
    }
    
    Ok(())
}

/// 递归复制目录
fn copy_dir_all(src: &Path, dst: &Path) -> io::Result<()> {
    fs::create_dir_all(&dst)?;
    
    for entry_result in fs::read_dir(src)? {
        let entry = entry_result?;
        let file_type = entry.file_type()?;
        let src_path = entry.path();
        let dst_path = dst.join(entry.file_name());
        
        if file_type.is_dir() {
            copy_dir_all(&src_path, &dst_path)?;
        } else {
            fs::copy(&src_path, &dst_path)?;
        }
    }
    
    Ok(())
}

fn main() -> io::Result<()> {
    // 解析命令行参数
    let args: Vec<String> = env::args().collect();
    let platform = if args.len() > 1 {
        match Platform::from_string(&args[1]) {
            Some(p) => p,
            None => {
                eprintln!("❌ 无效的平台参数: {}。可用选项: windows, linux, macos, all", args[1]);
                return Ok(());
            }
        }
    } else {
        // 默认构建所有平台
        Platform::All
    };
    
    // 获取客户端目录
    let client_dir = get_client_dir();
    if !client_dir.exists() {
        eprintln!("❌ 找不到客户端目录: {:?}", client_dir);
        return Ok(());
    }
    
    println!("📂 客户端目录: {:?}", client_dir);
    
    // 创建输出目录
    let output_dir = create_output_dir(&client_dir)?;
    println!("📂 输出目录: {:?}", output_dir);
    
    // 执行构建
    let platforms_to_build = match platform {
        Platform::All => vec![Platform::Windows, Platform::Linux, Platform::MacOS],
        _ => vec![platform],
    };
    
    for platform in platforms_to_build {
        let build_result = build_client(platform, &client_dir)?;
        
        if build_result.status.success() {
            println!("✅ {} 版本编译成功", platform.target_name());
        } else {
            eprintln!("❌ {} 版本编译失败", platform.target_name());
        }
        
        // 复制构建产物
        copy_build_artifacts(&build_result, &output_dir)?;
    }
    
    println!("🎉 构建完成！请在 {:?} 目录查看编译结果", output_dir);
    
    Ok(())
} 