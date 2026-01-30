import streamlit as st  # Streamlitをインポート
import pandas as pd  # pandasをインポート
import numpy as np  # numpyをインポート

# ページ設定
st.set_page_config(
    page_title="Data Noise Generator",  # ページタイトル
    page_icon="📊",  # ページアイコン
    layout="wide"  # ページレイアウト
)


# タイトル
st.title("📊 Data Noise Generator")  # タイトル
st.markdown("データ前処理テスト用の欠損値・異常値生成ツール")  # 説明文
st.markdown("---")

# Step1:CSVファイルのアップロード
st.header("Step 1: CSVファイルをアップロード")

uploaded_file = st.file_uploader(
    "CSVファイルを選択してください",  # ファイルアップローダーのラベル
    type=["csv"],  # ファイルの種類
    help="売上データなど、任意のCSVファイルをアップロードできます"  # ヘルプテキスト
)

if uploaded_file is not None:  # ファイルがアップロードされた場合
    # ファイルからデータの読み込み
    try:
        # ファイルサイズチェック：エラーハンドリング：5.2 処理エラー「メモリ不足」
        if uploaded_file.size > 200 * 1024 * 1024:  # 200MB
            st.error("❌ ファイルサイズが大きすぎます。200MB以下のファイルをアップロードしてください。")
            st.stop()
        
        # CSV読み込み
        df = pd.read_csv(uploaded_file)

        # 空ファイルチェック：エラーハンドリング：5.1入力検証「空ファイル」
        if len(df) == 0:
            st.error("❌ ファイルが空です。データが含まれるCSVをアップロードしてください。")
            st.stop()
        
        # 列が存在するかチェック：エラーハンドリング：5.1入力検証「列が存在しない」
        if len(df.columns) == 0:
            st.error("❌ CSVファイルに列が存在しません。正しい形式のCSVをアップロードしてください。")
            st.stop()

        st.success(f"✅ ファイルを読み込みました: {uploaded_file.name}")

        # Step2:データのプレビュー
        st.header("Step 2: 元データプレビュー")

        col1, col2 = st.columns(2)  # 2列に分割
        with col1:   # 行数
            st.metric("行数", f"{len(df):,d}件")  # 行数を表示
        with col2:  # 列数
            st.metric("列数", f"{len(df.columns):,d}列")  # 列数を表示

        # 最初の10行を表示
        st.subheader("データの確認（最初の10行）")
        st.dataframe(df.head(10))

        # データ型の表示
        st.subheader("データ型")
        dtype_df = pd.DataFrame({
            "列名": df.columns,
            "データ型": [str(dtype) for dtype in df.dtypes]
        })
        st.dataframe(dtype_df)

        # Step 3: ノイズ設定
        st.markdown("---")
        st.header("Step 3: ノイズ設定")

        # セッションステートの初期化
        if "noise_config" not in st.session_state:
            st.session_state.noise_config = {}
        
        st.subheader("欠損値設定")

        # 各列ごとに設定
        for col in df.columns: # 列ごとに設定
            with st.expander(f"列: {col} ({df[col].dtype})"):
                # 欠損値スライダー
                missing_rate = st.slider(
                    f"欠損率（%）",  # スライダーのタイトル
                    min_value=0,  # 最小値設定
                    max_value=100,  # 最大値設定
                    value=0,  # 初期値設定
                    key=f"missing_{col}"  # セッションステートのキー
                )
                # 設定を保存
                if col not in st.session_state.noise_config:  # セッションステートに設定がない場合
                    st.session_state.noise_config[col] = {}  # セッションステートに設定を初期化
                st.session_state.noise_config[col]["missing_rate"] = missing_rate  # セッションステートに設定を保存

                # 異常値スライダー
                st.markdown("---")
                anomaly_enabled = st.checkbox(  # 異常値を挿入するチェックボックス
                    "異常値を挿入",  # チェックボックスのラベル
                    key=f"anomaly_enabled_{col}"  # セッションステートのキー
                )

                if anomaly_enabled:  # 異常値を挿入するチェックボックスがオンの場合
                    anomaly_rate = st.slider(  # 異常値率をスライダーで設定
                        "異常値率（%）",  # スライダーのタイトル
                        min_value=0,  # 最小値設定
                        max_value=100,  # 最大値設定
                        value=5,  # 初期値設定
                        key=f"anomaly_rate_{col}"  # セッションステートのキー
                    )

                    # 合計チェック
                    total_rate = missing_rate + anomaly_rate  # 合計率を計算
                    if total_rate > 100:  # 合計率が100%を超えている場合：エラーハンドリング：5.1入力検証「欠損率+異常値率>100%」
                        st.error(f"⚠️ 欠損率({missing_rate}%) + 異常値率({anomaly_rate}%) = {total_rate}% が100%を超えています")  # エラーメッセージを表示
                    else:  # 合計率が100%以下の場合
                        st.info(f"💡 合計挿入率: {total_rate}%")

                    # 設定を保存
                    st.session_state.noise_config[col]["anomaly_rate"] = anomaly_rate  # 異常値率の設定をセッションステートに保存
                    st.session_state.noise_config[col]["anomaly_enabled"] = anomaly_enabled  # 異常値を挿入するチェックボックスの設定をセッションステートに保存

                    # データ型に応じた異常値パターン選択
                    st.write("**異常値のパターンを選択**")

                    anomaly_patterns = []  # 異常値パターンを保存するリスト

                    is_date_column = False # 日付型の列かどうか
                    if df[col].dtype == "object": #
                        # 日付形式化チェック
                        try:
                            pd.to_datetime(df[col].dropna().iloc[0])
                            is_date_column = True
                        except:
                            pass

                    # 日付型の場合
                    if is_date_column:
                        if st.checkbox("不正な日付形式", key=f"anomaly_invalid_date_{col}"):
                            anomaly_patterns.append("invalid_date")
                        if st.checkbox("未来の日付", key=f"anomaly_future_{col}"):
                            anomaly_patterns.append("future_date")
                        if st.checkbox("過去すぎる日付", key=f"anomaly_past_{col}"):
                            anomaly_patterns.append("past_date")
                    
                    # 数値型の場合
                    elif df[col].dtype in ["int64", "float64"]:  # 数値型の場合
                        if st.checkbox("マイナスの数値", key=f"anomaly_negative_{col}"):  # マイナスの数値を選択した場合
                            anomaly_patterns.append("negative")  # マイナスの数値をパターンに追加
                        if st.checkbox("平均の10倍", key=f"anomaly_large_{col}"):  # 平均の10倍を選択した場合
                            anomaly_patterns.append("large")  # 平均の10倍をパターンに追加
                        if st.checkbox("0(ゼロ)", key=f"anomaly_zero_{col}"):  # 0(ゼロ)を選択した場合
                            anomaly_patterns.append("zero")  # 0(ゼロ)をパターンに追加
                        if st.checkbox("文字列を挿入", key=f"anomaly_string_{col}"):  # 文字列を挿入を選択した場合
                            anomaly_patterns.append("string")  # 文字列をパターンに追加

                    # 文字列型の場合
                    elif df[col].dtype == "object":  # 文字列型の場合
                        if st.checkbox("数値を挿入", key=f"anomaly_number_{col}"):  # 数値を挿入を選択した場合
                            anomaly_patterns.append("number")  # 数値をパターンに追加
                        if st.checkbox("想定外の文字列", key=f"anomaly_custom_{col}"):  # 想定外の文字列を選択した場合
                            custom_string = st.text_input(  # カスタム文字列を入力するテキストボックス
                                "カスタム文字列",
                                value="INVALID",  # 初期値
                                key=f"anomaly_custom_text_{col}"  # セッションステートのキー
                            )
                            anomaly_patterns.append(f"custom:{custom_string}")  # カスタム文字列をパターンに追加
                    
                    # パターンを保存
                    st.session_state.noise_config[col]["anomaly_patterns"] = anomaly_patterns  # 異常値パターンをセッションステートに保存

                    if len(anomaly_patterns) == 0 and total_rate <= 100:
                        st.warning("⚠️ 異常値のパターンを1つ以上選択してください")
                else:
                    st.session_state.noise_config[col]["anomaly_rate"] = 0  # 異常値率の設定を0に設定
                    st.session_state.noise_config[col]["anomaly_enabled"] = False  # 異常値を挿入するチェックボックスの設定をFalseに設定

                if missing_rate > 0:
                    st.info(f"💡{len(df) * missing_rate // 100}件の欠損値が挿入されます")  # 欠損値の件数を表示

        # Step:4 プレビュー生成
        st.markdown("---")
        st.header("Step 4: プレビュー")

        if st.button("🔄 プレビュー生成", type="primary"):  # プレビュー生成ボタン
            # 異常値パターンが選択されているかチェック
            has_valid_config = False  # 異常値パターンが選択されているかのフラグ
            error_messages = []  # エラーメッセージを保存するリスト

            for col in df.columns:  # 列ごとにチェック
                if col in st.session_state.noise_config:  # セッションステートに設定がある場合
                    config = st.session_state.noise_config[col]  # セッションステートから、該当する列の設定を取得

                    # 欠損値または異常値が設定されているか
                    if config.get("missing_rate", 0) > 0:  # 欠損値が設定されている場合
                        has_valid_config = True  # 異常値パターンが選択されていることを示すフラグを立てる

                    if config.get("anomaly_enabled", False):  # 異常値を挿入するチェックボックスがオンの場合
                        if config.get("anomaly_rate", 0) > 0:  # 異常値率が0%以上の場合
                            patterns = config.get("anomaly_patterns", [])  # 異常値パターンを取得
                            # エラーハンドリング：5.1入力検証「異常値パターン未選択」
                            if len(patterns) == 0:  # 異常値パターンが選択されていない場合
                                error_messages.append(f"⚠️ {col}列: 異常値を挿入する場合は、パターンを1つ以上選択してください")  # エラーメッセージを追加
                            else:  # 異常値パターンが選択されている場合
                                has_valid_config = True  # 異常値パターンが選択されていることを示すフラグを立てる
            # エラーメッセージ表示
            if error_messages:  # エラーメッセージがある場合
                for msg in error_messages:  # エラーメッセージごとに表示
                    st.error(msg)  # エラーメッセージを表示
            
            # 何も設定されていない場合
            if not has_valid_config:  # 異常値パターンが選択されていない場合
                st.warning("⚠️ 欠損値または異常値が設定されていません。設定を確認してください。")  # エラーメッセージを表示
                st.stop()  # アプリケーションを停止


            # データをコピー
            df_noisy = df.copy()

            # 各列に欠損値を挿入
            for col in df.columns:  # 列ごとに欠損値を挿入
                if col in st.session_state.noise_config:  # セッションステートに設定がある場合
                    missing_rate = st.session_state.noise_config[col].get("missing_rate", 0)  # セッションステートから、該当する列の欠損率を取得

                    if missing_rate > 0:  # 欠損率が0%以上の場合
                        # 欠損値を挿入する行をランダムに選択
                        n_missing = int(len(df) * missing_rate / 100)  # 欠損値を挿入する行数を計算
                        missing_indices = np.random.choice( # 欠損値を挿入する行をランダムに選択
                            df.index, # 行インデックス
                            size=n_missing, # 欠損値を挿入する行数
                            replace=False # 重複を許可しない
                        )
                        df_noisy.loc[missing_indices, col] = np.nan # 欠損値を挿入
            
                    # 各列に異常値を挿入
                    config = st.session_state.noise_config[col]  # セッションステートから、該当する列の設定を取得

                    if config.get("anomaly_enabled", False):  # 異常値を挿入するチェックボックスがオンの場合
                        anomaly_rate = config.get("anomaly_rate", 0)  # 異常値率を取得
                        anomaly_patterns = config.get("anomaly_patterns", [])  # 異常値パターンを取得

                        if anomaly_rate > 0 and len(anomaly_patterns) > 0:  # 異常値率が0%以上、かつ、異常値パターンが1つ以上ある場合
                            # 異常値を挿入する行数を計算
                            n_anomaly = int(len(df) * anomaly_rate / 100)  # 異常値を挿入する行数を計算

                            # すでに欠損値が入っている行を除外
                            available_indices = df_noisy[df_noisy[col].notna()].index  # 欠損値が入っていない行を取得

                            if len(available_indices) > 0 and len(available_indices) >= n_anomaly:  # 欠損値が入っている行があり、かつ、異常値を挿入する行数がある場合
                                # ランダムに行を選択
                                anomaly_indices = np.random.choice(
                                    available_indices, # 欠損値が入っていない行を取得
                                    size=n_anomaly, # 異常値を挿入する行数
                                    replace=False # 重複を許可しない
                                )

                                # パターンごとに均等に配分
                                n_per_pattern = max(1, n_anomaly // len(anomaly_patterns))

                                for i, pattern in enumerate(anomaly_patterns):  # 異常値パターンごとに均等に配分
                                    start_idx = i * n_per_pattern  # 開始インデックス
                                    end_idx = start_idx + n_per_pattern if i < len(anomaly_patterns) - 1 else n_anomaly  # 終了インデックス
                                    pattern_indices = anomaly_indices[start_idx:end_idx]  # 異常値を挿入する行を取得

                                    # 数値型の異常値
                                    if pattern == "negative":
                                        # 元の列の型に合わせて変換
                                        df_noisy.loc[pattern_indices, col] = -abs(df_noisy.loc[pattern_indices, col])  # マイナスの数値を挿入
                                    elif pattern == "large":
                                        # 元の列の型に合わせて変換
                                        value = df[col].mean() * 10  # 平均値の10倍を挿入
                                        if df[col].dtype == 'int64':
                                            value = int(value)  # 整数型に変換
                                        df_noisy.loc[pattern_indices, col] = value  # 平均値の10倍を挿入
                                    elif pattern == "zero":
                                        df_noisy.loc[pattern_indices, col] = 0  # 0を挿入
                                    elif pattern == "string":
                                        # 文字列を挿入する場合は列の型を変更
                                        df_noisy[col] = df_noisy[col].astype('object')  # 列の型を変更
                                        df_noisy.loc[pattern_indices, col] = "ERROR"  # 文字列を挿入

                                    # 文字列型の異常値
                                    elif pattern == "number":
                                        df_noisy.loc[pattern_indices, col] = 9999  # 数値を挿入
                                    elif pattern.startswith("custom:"): # カスタム文字列を挿入する場合
                                        custom_value = pattern.split(":", 1)[1]  # カスタム文字列を取得
                                        df_noisy.loc[pattern_indices, col] = custom_value  # カスタム文字列を挿入
                                    
                                    # 日付型の異常値
                                    elif pattern == "invalid_date":  # 不正な日付形式を挿入する場合
                                        df_noisy.loc[pattern_indices, col] = "INVALID_DATE"  # 不正な日付形式を挿入
                                    elif pattern == "future_date":  # 未来の日付を挿入する場合
                                        df_noisy.loc[pattern_indices, col] = "2100-01-01"  # 未来の日付を挿入
                                    elif pattern == "past_date":  # 過去すぎる日付を挿入する場合
                                        df_noisy.loc[pattern_indices, col] = "1900-01-01"  # 過去すぎる日付を挿入


            # プレビュー表示
            st.subheader("ノイズ挿入後のデータ")

            # 統計情報
            col1, col2, col3 = st.columns(3)  # 2列に分割
            with col1:  # 元データ行数
                st.metric("元データ行数", f"{len(df):,d}件")  # 元データ行数を表示
            with col2:  # 挿入された欠損値
                total_missing = df_noisy.isnull().sum().sum()  # 欠損値の件数を計算
                st.metric("挿入された欠損値", f"{total_missing:,d}件")  # 欠損値の件数を表示
            with col3:  # 欠損率
                total_cells = len(df) * len(df.columns)  # 全セル数を計算
                missing_rate = (total_missing / total_cells) * 100  # 欠損率を計算
                st.metric("全体欠損率", f"{missing_rate:.2f}%")  # 欠損率を表示

            # データ表示
            st.subheader("ノイズ挿入後のデータ（最初の20行）") # ノイズ挿入後のデータを表示
            st.dataframe(df_noisy.head(20)) # ノイズ挿入後のデータを10行表示

            # 欠損値がある行を表示
            st.subheader("欠損値を含む行（最初の10行）") # 欠損値を含む行を表示
            missing_rows = df_noisy[df_noisy.isnull().any(axis=1)]  # 欠損値を含む行を取得
            if len(missing_rows) > 0:  # 欠損値を含む行がある場合
                st.dataframe(missing_rows.head(10))  # 欠损值を含む行の10行（最大）を表示
                st.info(f"💡 欠損値を含む行: {len(missing_rows)}行")  # 欠損値を含む行の件数を表示
            else:  # 欠損値を含む行がない場合
                st.info("💡 欠損値を含む行はありません")  # 欠損値を含む行がないことを表示

            # 列ごとの欠損率
            with st.expander("📊 列ごとの欠損率を表示"):
                missing_by_col = df_noisy.isnull().sum()  # 列ごとの欠損数を計算
                
                # 欠損数でフィルタを行う
                missing_by_col_filtered = missing_by_col[missing_by_col > 0]  # 欠損数が0以上の列を取得

                # その後DataFrameを作成（文字列に変換）
                missing_rate_df = pd.DataFrame({
                    "列名": missing_by_col_filtered.index,  # 列名
                    "欠損数": missing_by_col_filtered.values,  # 欠損数
                    "欠損率": [f"{rate:.2f}%" for rate in (missing_by_col_filtered / len(df) * 100).values]  # 欠損率
                })
                if len(missing_rate_df) > 0:  # 欠損率が0%以上の列がある場合
                    st.dataframe(missing_rate_df, width="stretch")
                else:  # 欠損率が0%以上の列がない場合
                    st.info("欠損値がある列はありません")

            # セッションステートに保存
            st.session_state.df_noisy = df_noisy

            # Step 5: ダウンロード
            st.markdown("---")
            st.header("Step 5: ダウンロード")

            # CSVに変換
            csv = df_noisy.to_csv(index=False).encode("utf-8")

            # ファイル名生成
            original_filename = uploaded_file.name.replace(".csv", "")  # 元ファイル名を取得
            noisy_filename = f"{original_filename}_noisy.csv"  # ノイズ入りファイル名を生成

            # ダウンロードボタン
            st.download_button(
                label="📥 ノイズ入りCSVをダウンロード",  # ダウンロードボタンのラベル
                data=csv,  # CSVデータ
                file_name=noisy_filename,  # ファイル名
                mime="text/csv",  # MIMEタイプ
                type="primary"  # ボタンの種類
            )

            st.success(f"✅ {noisy_filename} としてダウンロード完了できます")

    except Exception as e:
        st.error(f"❌ ファイルの読み込みに失敗しました: {e}")
