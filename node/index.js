import { exec } from "child_process";

exec("python python/main.py", (err) => {
  if (err) console.error(err);
  else console.log("Video generado");
});
