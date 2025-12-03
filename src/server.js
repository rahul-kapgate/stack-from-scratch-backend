import app from "./app.js";
import { ENV } from "./config/env.js";

app.listen(ENV.PORT, () => {
  console.log(`🚀 Server listening on port ${ENV.PORT} (${ENV.NODE_ENV})`);
});

