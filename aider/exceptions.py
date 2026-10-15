from dataclasses import dataclass

from aider.dump import dump  # noqa: F401


@dataclass
class ExInfo:
    name: str
    retry: bool
    description: str


EXCEPTIONS = [
    ExInfo("APIConnectionError", True, None),
    ExInfo("APIError", True, None),
    ExInfo("APIResponseValidationError", True, None),
    ExInfo(
        "AuthenticationError",
        False,
        "The API provider is not able to authenticate you. Check your API key.",
    ),
    ExInfo("AzureOpenAIError", True, None),
    ExInfo("BadGatewayError", True, "The API provider's servers are down or overloaded."),
    ExInfo("BadRequestError", False, None),
    ExInfo("BudgetExceededError", True, None),
    ExInfo(
        "ContentPolicyViolationError",
        True,
        "The API provider has refused the request due to a safety policy about the content.",
    ),
    ExInfo("ContextWindowExceededError", False, None),  # special case handled in base_coder
    ExInfo("ImageFetchError", False, "The API provider was unable to fetch one or more images."),
    ExInfo("InternalServerError", True, "The API provider's servers are down or overloaded."),
    ExInfo("InvalidRequestError", True, None),
    ExInfo("JSONSchemaValidationError", True, None),
    ExInfo("NotFoundError", False, None),
    ExInfo(
        "PermissionDeniedError",
        False,
        "Permission was denied. Check your API key and/or credentials.",
    ),
    ExInfo("OpenAIError", True, None),
    ExInfo(
        "RateLimitError",
        True,
        "The API provider has rate limited you. Try again later or check your quotas.",
    ),
    ExInfo("RouterRateLimitError", True, None),
    ExInfo("ServiceUnavailableError", True, "The API provider's servers are down or overloaded."),
    ExInfo("UnprocessableEntityError", True, None),
    ExInfo("UnsupportedParamsError", True, None),
    ExInfo(
        "Timeout",
        True,
        "The API provider timed out without returning a response. They may be down or overloaded.",
    ),
]


class LiteLLMExceptions:
    exceptions = dict()
    exception_info = {exi.name: exi for exi in EXCEPTIONS}

    def __init__(self):
        """Initialize and populate the LiteLLM exception mapping.

        Pre-conditions:
            - None.

        Post-conditions:
            - self.exceptions contains mapping of resolved exception classes to ExInfo instances.

        Raises:
            - None.
        """
        self._load()

    def _load(self, strict=False):
        """Load and resolve exception classes from litellm and underlying HTTP/OpenAI modules.

        Pre-conditions:
            - litellm package is importable in the active environment.
            - strict is a boolean indicating whether unrecognized errors raise ValueError.

        Post-conditions:
            - self.exceptions dictionary is populated mapping Exception classes to ExInfo instances.
            - Missing attributes in litellm do not raise AttributeError.

        Raises:
            - ValueError: If strict=True and a litellm Error class is not present in self.exception_info.
        """
        import litellm

        if strict:
            for var in dir(litellm):
                # Filter by BaseException because instances of non-exception classes cannot be caught.
                if var.endswith("Error"):
                    try:
                        attr = getattr(litellm, var, None)
                        if isinstance(attr, type) and issubclass(attr, BaseException):
                            if var not in self.exception_info:
                                raise ValueError(f"{var} is in litellm but not in aider's exceptions list")
                    except TypeError:
                        pass

        for var in self.exception_info:
            ex = getattr(litellm, var, None)
            if ex is None and hasattr(litellm, "exceptions"):
                ex = getattr(litellm.exceptions, var, None)
            if ex is not None and isinstance(ex, type) and issubclass(ex, BaseException):
                self.exceptions[ex] = self.exception_info[var]

        # Also capture raw network connection and timeout errors from underlying libraries
        try:
            import httpx
            self.exceptions[httpx.ConnectError] = ExInfo("ConnectError", True, "Connection to LLM server failed.")
            self.exceptions[httpx.ReadTimeout] = ExInfo("ReadTimeout", True, "LLM server timed out.")
            self.exceptions[httpx.ConnectTimeout] = ExInfo("ConnectTimeout", True, "Connection to LLM server timed out.")
        except ImportError:
            pass

        try:
            import openai
            self.exceptions[openai.APIConnectionError] = ExInfo("APIConnectionError", True, "Cannot connect to LLM server.")
            self.exceptions[openai.InternalServerError] = ExInfo("InternalServerError", True, "LLM server returned an error.")
        except ImportError:
            pass

    def exceptions_tuple(self):
        """Return tuple of all registered exception classes suitable for except clauses.

        Pre-conditions:
            - None.

        Post-conditions:
            - Returns tuple of Exception types.

        Raises:
            - None.
        """
        return tuple(self.exceptions)

    def get_ex_info(self, ex):
        """Return the ExInfo for a given exception instance.

        Pre-conditions:
            - ex is an instance of BaseException.

        Post-conditions:
            - Returns a valid ExInfo instance describing the retryability and description of ex.

        Raises:
            - None.
        """
        import litellm

        if hasattr(litellm, "APIConnectionError") and isinstance(ex, litellm.APIConnectionError):
            if "boto3" in str(ex):
                return ExInfo("APIConnectionError", False, "You need to: pip install boto3")
            if "OpenrouterException" in str(ex) and "'choices'" in str(ex):
                return ExInfo(
                    "APIConnectionError",
                    True,
                    (
                        "OpenRouter or the upstream API provider is down, overloaded or rate"
                        " limiting your requests."
                    ),
                )

        # Check for specific non-retryable APIError cases like insufficient credits
        if hasattr(litellm, "APIError") and isinstance(ex, litellm.APIError):
            err_str = str(ex).lower()
            if "insufficient credits" in err_str and '"code":402' in err_str:
                return ExInfo(
                    "APIError",
                    False,
                    "Insufficient credits with the API provider. Please add credits.",
                )
            # Fall through to default APIError handling if not the specific credits error

        # Map vLLM / OpenAI-compatible context window errors
        err_str = str(ex).lower()
        if (
            "maximum context length is" in err_str
            or "context_length_exceeded" in err_str
            or "too many tokens" in err_str
            or "prompt is too long" in err_str
        ):
            return ExInfo(
                "ContextWindowExceededError",
                False,
                "Context limit exceeded on LLM server.",
            )

        # Direct class lookup
        if ex.__class__ in self.exceptions:
            return self.exceptions[ex.__class__]

        # Subclass lookup
        for exc_cls, info in self.exceptions.items():
            if isinstance(ex, exc_cls):
                return info

        # Fallback string pattern checks for cluster/server startup & bad gateway errors
        if any(term in err_str for term in (
            "502 bad gateway", "bad gateway", "connection refused", "connecterror",
            "failed to connect", "service unavailable", "503 service unavailable",
            "remote disconnected", "server disconnected"
        )):
            return ExInfo(ex.__class__.__name__, True, "The LLM server is starting up or temporarily unavailable.")

        return self.exceptions.get(ex.__class__, ExInfo(None, None, None))
