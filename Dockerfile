FROM python:3.10-slim AS base

FROM base AS install
COPY ./src/requirements.txt /src/requirements.txt
WORKDIR /src
RUN python -m pip install -r requirements.txt

FROM install AS build
COPY ./src /src
COPY ./app /app

FROM build AS final
COPY --from=build /src /src
COPY --from=build /app /app
WORKDIR /app
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
ENV ASPNETCORE_hostBuilder:reloadConfigOnChange=false
ENV UNITE_COMMAND="python"
ENV UNITE_COMMAND_ARGUMENTS="-u app.py {data}/{proc}"
ENV UNITE_SOURCE_PATH="/src"
ENV UNITE_DATA_PATH="/mnt/data"
ENV UNITE_PROCESS_LIMIT="10"
EXPOSE 80
CMD ["/app/Unite.Commands.Web", "--urls", "http://0.0.0.0:80"]
