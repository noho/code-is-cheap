这是已授权的普通合成 live 工具链验收，不是仓库开发或业务任务。只处理指定输入和一个新结果文件，不委派、不读其他文件、不修改输入、不提交或部署。
必须按顺序执行三个独立工具步骤：
1. 用工具完整读取 /private/tmp/codex-recovered-timeout-demand/probes/codex/input.json。
2. 用工具运行实际 Python 程序，从输入 JSON 的 values 计算 count、sum、sum_squares，复制 nonce，并以输入文件原始字节计算 input_sha256。以 JSON 写入新文件 /private/tmp/codex-recovered-timeout-demand/probes/codex/result.json，使用独占新建防止覆盖。不要凭心算给结果。
3. 再用工具完整读回 /private/tmp/codex-recovered-timeout-demand/probes/codex/result.json，核对程序输出。
最终答复简短说明读回结果和产物路径，并独立一行 CANARY=<从输入读取的nonce>。必须有实际工具结果记录，不能只描述命令。此 probe 不注入或声称复现真实网络故障。
