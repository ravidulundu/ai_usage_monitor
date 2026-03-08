module.exports = {
  root: true,
  extends: ["eslint:recommended"],
  plugins: ["jsdoc"],
  env: {
    es2022: true
  },
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  },
  globals: {
    log: "readonly",
    logError: "readonly",
    global: "readonly"
  },
  rules: {
    "no-console": "off",
    "consistent-return": "error",
    "no-implicit-globals": "error",
    "prefer-const": "error",
    "no-unused-vars": [
      "error",
      {
        args: "after-used",
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_"
      }
    ]
  },
  overrides: [
    {
      files: ["gnome-extension/aiusagemonitor@aimonitor/**/*.js"],
      settings: {
        jsdoc: {
          mode: "typescript"
        }
      },
      rules: {
        "jsdoc/check-types": "error",
        "jsdoc/valid-types": "error"
      }
    },
    {
      files: ["gnome-extension/aiusagemonitor@aimonitor/popupSelection.js"],
      rules: {
        "jsdoc/require-jsdoc": [
          "error",
          {
            publicOnly: true,
            require: {
              FunctionDeclaration: true,
              MethodDefinition: false,
              ClassDeclaration: false,
              ArrowFunctionExpression: false,
              FunctionExpression: false
            }
          }
        ],
        "jsdoc/require-param-type": "error",
        "jsdoc/require-returns-type": "error"
      }
    }
  ]
};
